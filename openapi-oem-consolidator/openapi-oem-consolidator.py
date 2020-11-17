#! /usr/bin/env python3

## This tool consolidates the OEM's OpenAPI YAML file with Redfish Bundle.

import argparse;
import glob;
import os;
import pprint;
import re;
import sys;
import shutil;
import yaml;

dbg = False;
err_count = 0;
dbg_pp = None;

def dbg_print(dbg_text):
  global dbg;

  if dbg:
    print("[DEBUG]: ", end="");
    print(dbg_text);

def dbg_dict_pretty_print(indent, obj):
  hdr = "[DEBUG]: ";

  for key, value in obj.items():
    print(hdr + ("  " * indent) + str(key) + " : ", end="");
    
    if (isinstance(value, dict)):
      print("{");
      dbg_dict_pretty_print(indent + 1, value);
      print(hdr + ("  " * indent) + "}");
    else:
      print(str(value));

  return;

def dbg_pprint(dbg_title, obj):
  global dbg;
  global dbg_pp;

  if dbg:
    print("[DEBUG]: ", end="");
    print(dbg_title + ":");

    if isinstance(obj, dict):
      dbg_dict_pretty_print(0, obj);
    else: 
      dbg_pp.pprint(obj);

  return;

def err_print(err_type, err_txt):
  global err_count;

  if err_type == 1:
    print("[ERROR SUMMARY]: ", end="");
  else:
    print("[ERROR #" + str(err_count)+ "]: ", end="");
    err_count += 1;

  print(err_txt);

def check_redfish_dir(basepath):
  # This is a simple sanity check that the directory provided is a Redfish
  # DSP8010 directory. In other words, an extracted DSP8010 directory.

  if (not os.path.isdir(os.path.join(basepath, "openapi"))) or \
     (not os.path.isdir(os.path.join(basepath, "csdl"))) or \
     (not os.path.isdir(os.path.join(basepath, "json-schema"))) or \
     (not os.path.isdir(os.path.join(basepath, "dictionaries"))) or \
     (not os.path.isfile(os.path.join(basepath, "openapi", "openapi.yaml"))):
    return 1;

  return 0;

def check_oem_dir(basepath):

  if not os.path.isfile(os.path.join(basepath, "openapi.yaml")):
    return 1;

  return 0;


def copy_redfish_yaml_to_output(src, dst):

  shutil.copytree(os.path.join(src, "openapi"), dst, dirs_exist_ok=True);

def read_oem_directory(oem_dir):

  oem_files = os.listdir(path=oem_dir);
  return oem_files;

def parse_redfish_resource_name(name):
  # This function splits out the base resource name and its version
  # from the YAML file name.
  resource_info = {};

  bname = os.path.basename(name);
  pat = re.compile("^(.+)\.v([0-9]+_[0-9]+_[0-9]+)\.yaml");

  match = pat.search(bname);

  if match:
    resource_info["resource"] = match.group(1);
    resource_info["version"] = match.group(2);

  dbg_pprint("Resource Info", resource_info);

  return resource_info;

def do_search_and_replace_helper(oem_filename, rf_filename, patterns,
                                 oem_yaml, redfish_yaml, yaml_path,
                                 resource_info, ignore_ver):
  
  for key, value in oem_yaml.items():
    new_yaml_path = yaml_path + "/" + str(key);
    
    dbg_print("key: " + str(key));
    dbg_print("Processing YAML Path: " + new_yaml_path);

    if not key in redfish_yaml:
      missing = 1;

      # Check to see if this property's name has a version string.
      if ignore_ver and patterns["ver"].search(key):
        sub_value = "_v" + resource_info["version"] + "_";
        key = patterns["ver"].sub(sub_value, key);
        dbg_print("New Key Name: " + key);

        if key in redfish_yaml:
          missing = 0;
      
      if missing:
        err_print(0, oem_filename + ": YAML path, " + new_yaml_path + 
                  ", not found in " + rf_filename);
        return ;

    if (key == "Oem") or \
       (key == "OEM") or \
       (key == "Resource_Oem") or \
       (patterns["oem"].search(key)): 
      dbg_print("Found Matching OEM YAML path: " + new_yaml_path);
      dbg_pprint("Value for Matching OEM YAML path", value);
      redfish_yaml[key] = value;
      return;

    do_search_and_replace_helper(oem_filename, rf_filename, patterns, value, 
                                 redfish_yaml[key], new_yaml_path, 
                                 resource_info, ignore_ver);

  return ;

def do_search_and_replace(output_dir, oem_filename, rf_filename, oem_yaml, 
                          redfish_yaml, ignore_ver):

  patterns = {};
  patterns["oem"] = re.compile("OemActions$");
  patterns["ver"] = re.compile("_v[0-9]+_[0-9]+_[0-9]+_");

  resource_info = parse_redfish_resource_name(rf_filename);

  do_search_and_replace_helper(oem_filename, rf_filename, patterns, oem_yaml, 
                               redfish_yaml, "", resource_info, ignore_ver);

  new_rf_data = yaml.dump(redfish_yaml);

  with open (os.path.join(output_dir, rf_filename), "w") as rf:
    rf.write(new_rf_data);

  return;

def do_single_substitution(src_dir, output_dir, of, rf, txt_hdr, ignore_ver):
  oem_file = os.path.join(src_dir, of);
  rf_file = os.path.join(output_dir, rf);
  err = False;

  with open(oem_file, 'r') as f:
    input_data = f.read();

  with open(rf_file, 'r') as r:
    rf_data = r.read();

  f.close();
  r.close();

  print(txt_hdr + "Parsing " + of + ". ** This may take a while. **");
  oem_yaml = yaml.safe_load(input_data);

  if (not isinstance(oem_yaml, dict)):
    err_print(0, of + "does not contain any yaml data.");
    err = True;
  else:
    dbg_pprint("OEM " + of + " YAML", oem_yaml);


  print(txt_hdr +  "Parsing " + rf + ". ** This may take a while. **");
  rf_yaml = yaml.safe_load(rf_data);

  if (not isinstance(rf_yaml, dict)):
    err_print(0, rf + "does not contain any yaml data.");
    err = True;
  else:
    dbg_pprint("Refish " + rf + " YAML", rf_yaml);

  if not err:
    do_search_and_replace(output_dir, of, rf, oem_yaml, rf_yaml, ignore_ver);

  return;


def do_multiple_substitutions(src_dir, output_dir, of, resource):
  # This function does multiple substitions. It substitues all versions for 
  # a given Redfish resource.
  resource_filter = resource + ".v*.yaml";

  matching_files = glob.glob(os.path.join(output_dir, resource_filter));

  for rf in matching_files:
    base_rf = os.path.basename(rf);
    print("    Processing versioned Redfish resource: " + base_rf);
    do_single_substitution(src_dir, output_dir, of, base_rf, "      ", True);

def process_openapi(oem_dir, output_dir):
  err = False;

  with open(os.path.join(oem_dir, "openapi.yaml"), 'r') as oem:
    oem_data = oem.read();

  with open(os.path.join(output_dir, "openapi.yaml"), 'r') as rf:
    rf_data = rf.read();

  oem.close();
  rf.close();

  print("  Parsing OEM OpenAPI. ** This may take a while. **");
  oem_yaml = yaml.safe_load(oem_data);

  if (not isinstance(oem_yaml, dict)):
    err_print(0, "OEM's openapi.yaml does not contain any yaml data.");
    err = True;

  print("  Parsing Redfish OpenAPI. ** This may take a while. **");
  rf_yaml = yaml.safe_load(rf_data);

  if (not isinstance(rf_yaml, dict)):
    err_print(0, "Redfish's openapi.yaml does not contain any yaml data.");
    err = True;

  if err:
    return;

  print("  Checking OEM's OpenAPI requirements.");

  ## If components exist in OEM openapi.yaml, print an error.
  if "components" in oem_yaml:
    err_print(0, "OEM's openapi.yaml is prohibited from having components " +
              "section.");
    err = True;

  ## Check Info section.
  if not "info" in oem_yaml:
    err_print(0, "OEM's openapi.yaml is missing 'info' section.");
    err = True;
  else:
    ## Replace the info section completely with the OEM's info section.
    rf_yaml["info"] = oem_yaml["info"];

  ## Check open api version.
  if not "openapi" in oem_yaml:
    err_print(0, "OEM's openapi.yaml is missing 'openapi' section.");
    err = True;

  if not "openapi" in rf_yaml:
    err_print(0, "Redfish's openapi.haml is missing 'openapi' section.");
    err = True;

  ## Check that open api versions match.
  if ("openapi" in oem_yaml) and \
     ("openapi" in rf_yaml):
    if oem_yaml["openapi"] != rf_yaml["openapi"]:
      err_print(0, "OEM and Redfish openapi versions do not match. " +
                "Redfish's OpenAPI version: " + rf_yaml["openapi"] + ". " +
                "OEM's OpenAPI version: " + oem_yaml["openapi"] );
      err = True;
  
  ## Process the paths section.
  if "paths" in oem_yaml:
    if "paths" in rf_yaml:
      rf_yaml["paths"].update(oem_yaml["paths"]);
    else:
      err_print(0, "Redfish's openapi is missing 'paths' section.");
      err = True;

  if not err:
    print("  Writing consolidated OEM and Redfish openapi.yaml.");
    
    rf_data = yaml.dump(rf_yaml);

    with open(os.path.join(output_dir, "openapi.yaml"), "w") as out:
      out.write(rf_data);

    out.close();

  return;

def process_oem_files(oem_dir, oem_files, dst_dir):
  # This is the core logic for processing the OEM OpenAPI directory.
  
  single = re.compile(".+-OEM\.yaml$");
  single_ver = re.compile(".+-OEM\.v[0-9]+_[0-9]+_[0-9]+\.yaml$");
  all_vers = re.compile(".+-OEM\.all-vers\.yaml$");
  ignore_files = re.compile("^\..*$");
  multiple_files = 0;

  for f in oem_files:
    print("Processing OEM file: " + f);
    multiple_files = 0;

    if ignore_files.search(f):
      print("  Ignored. Skipping.");
      print("");
      continue;

    if f == "openapi.yaml":
      process_openapi(oem_dir, dst_dir);
      print("");
      continue;

    if single.search(f):
      rf_basename = re.sub("-OEM\.yaml$", ".yaml", f);
    elif single_ver.search(f):
      rf_basename = re.sub("-OEM\.v", ".v", f);
    elif all_vers.search(f):
      multiple_files = 1;
      rf_basename = re.sub("-OEM\.all-vers\.yaml", "", f);
    else:
      rf_basename = "";

    if (rf_basename == ""):
      # Just copy the file over to output directory
      shutil.copy2(os.path.join(oem_dir, f), dst_dir);
      print("  Copying file to " + dst_dir + ".");
    elif multiple_files:
      print("  Replacing all versions of " + rf_basename + ".");
      do_multiple_substitutions(oem_dir, dst_dir, f, rf_basename);
    else:
      print("  Replacing single file or single versione of " + rf_basename +
            " resource.");
      do_single_substitution(oem_dir, dst_dir, f, rf_basename, "    ", False);

    print("");

def main():
  global dbg;
  global err_count;
  global dbg_pp;

  # Create Command Line Parameters
  desc_text = (f"Consolidates OEM's OpenAPI bundle with Redfish OpenAPI bundle "
                "into a single OpenAPI bundle. For detailed help, please "
                "consult README.md.\n"
                "Positional arguments are required.\n"
                "");
  parser = argparse.ArgumentParser(description=desc_text);
  parser.add_argument('redfish_dir', action='store', 
                      help=('Specifies the directory of the extracted Redfish '
                            'DSP8010 bundle.'));
  parser.add_argument('oem_dir', action='store', 
                      help='Specifies the OEM directory.');
  parser.add_argument('output_dir',  action='store', 
                      help=(
                        'Specifies the consolidated (i.e., output) directory. '
                        'This directory will be created.'));
  parser.add_argument('--debug', required=False, action='store_true', 
                      default=False,
                      help="Enabled debug messages.");
  parser.add_argument('--remove-output-dir', required=False, 
                      action='store_true', default=False,
                      help="Remove the output directory if it exists.");

  args = parser.parse_args();
  dbg = args.debug;
  err = 0;

  if dbg:
    dbg_pp = pprint.PrettyPrinter(indent=1, compact=False);

  dbg_pprint("Arugments Passed In", args);
  redfish_dir = args.redfish_dir;
  oem_dir = args.oem_dir;
  output_dir = args.output_dir;

  # Let's check that the "input" directory exists.
  if not os.path.isdir(redfish_dir):
    err_print(0, "The directory, " + redfish_dir + " does not exist.");
    err = 1;

  if not os.path.isdir(oem_dir):
    err_print(0, "The directory, " + oem_dir + " does not exist.");
    err = 1;

  # Make sure the output directory does not exist to ensure we do not 
  # screw up an existing directory.
  if os.path.isdir(output_dir):
    if args.remove_output_dir:
      shutil.rmtree(output_dir);
    else:
      err_print(0, "The directory, " + output_dir + " exists. Since this is " +
                 "an output " + "directory, please remove the directory or " +
                 "specify another directory.");
      err = 1;

  if check_redfish_dir(redfish_dir):
    err_print(0, redfish_dir + 
              " is not an extracted Redfish DSP8010 bundle directory.");
    err = 1;

  if check_oem_dir(oem_dir):
    err_print(0, oem_dir + " does not contain openapi.yaml.");
    err = 1;

  if err:
    err_print(1, "There were " + str(err_count) + " error(s) encountered.");
    sys.exit(-1);

  err = 0;

  # Let's create the output directory.
  try:
    os.makedirs(output_dir);
  except OSError:
    print("Cannot create directory " + output_dir + ".");
    sys.exit(-1);
  else:
    print("Successfully created directory " + output_dir + ".");

  print("");
  copy_redfish_yaml_to_output(redfish_dir, output_dir);
  files = read_oem_directory(oem_dir);
  process_oem_files(oem_dir, files, output_dir);

  if err_count:
    err_print(1, "There were " + str(err_count) + " error(s) encountered.");
    sys.exit(-1);

  print("*****************************************************");
  print("Redfish and OEM OpenAPI Consolidation was successful.");
  print("*****************************************************");
  print("");
  sys.exit(0);

main()
