const glob = require('glob');
const path = require('path');
const assert = require('assert');
const fs = require('fs');
const config = require('config');
const process = require('process');
const CSDL = require('CSDLParser');
const SpellChecker = require('spellchecker');

var options = {useLocal: [config.get('Redfish.CSDLDirectory'), path.normalize(__dirname+'/fixtures')],
               useNetwork: true};

if(config.has('Redfish.AdditionalSchemaDirs')) {
  options.useLocal = options.useLocal.concat(config.get('Redfish.AdditionalSchemaDirs'));
}

//Setup a global cache for speed
options.cache = new CSDL.cache(options.useLocal, options.useNetwork);

const OverRideFiles = ['http://redfish.dmtf.org/schemas/swordfish/v1/Volume_v1.xml'];

//These are words we want to allow for any/all files
const WordAllowList = ["AccountLockoutThreshold", "ActionInfo", "ACK", "ACL", "ACPI", "AdditionalProperties", "AddressOrigin", "AHCI", "AES", "aggregate's", "aggregator",
                       "AllocatedBytes", "AllowableValues", "API", "APIs", "ARP", "anycast", "ASIC", "ASICs", "ASN", "ASNs", "ATA", "ASHRAE", "AttributeName", "AttributeType",
                       "attribute's",  "autoconfiguration", "autoconfigured", "AutoExpand", "autonegotiate", "autonegotiating", "autonegotiation", "backpressure", "BFD", "BGP", "BMC", "BMCs",
                       "BootOptionReference", "bootable", "BootOrder", "BOOTP", "cancelled", "cancelling", //British spelling is fine
                       "CEE", "chipset", "CIFS", "ciphertext", "CLI", "CLP", "colocated", "ComplexTypes", "ComponentIntegrity", "composable", "composition", "ComputerSystem", "ComputerSystems",
                       "coprocessor", "conformant", "ConsumedBytes", "ContainedBy", "Contoso", "CRC", "CRCs", "CRLs", "CSDL", "CXL", "DataSourceUri", "DateTime", "DateTimeOffset", "DCB",
                       "DCIM", "DDR", "deduplication", "dereferenceable", "DHCP", "DIMM", "DIMMs", "drive's", "DMTF", "DNS", "downloadable", "DriveFailed", "DVD", "dword", "dwords", "ECC", "ECMA",
                       "ECN", "EDSFF", "EEE", "EFI", "EIA", "ElectricalContext", "EntryType",  "ESI", "ETag", "EthernetInterface", "EthernetInterfaceType", "endian", "EntityRole",
                       "EnumMember", "EnumType", "EnumTypes", "EUI", "EventRecord", "EventType", "EVI", "EVPN", "FabricAdapter", "failover", "fallback", "FC", "FCoE",
                       "Fibre", "FibreChannel", //British spelling is needed
                       "FICON", "FIP", "FPGA", "ForceRestart", "ForceOff", "FQDN", "FrequencyMHz", "FrequencyMhz", "FRU", "Gbit", "GenZ", "GiB", "gigabit", "gibibytes", "GPS", "GPU", "GracefulRestart",
                       "GroupType", "GUID", "GUIDs", "HH", "HMAC", "HostingRoles", "hotkey", "hotplug", "HTTP", "HTTPS", 
                       "hypervisor", "IANA", "IEC", "IEEE's", "IETF", "IGP", "IP", "IPMI", "INCITS", "IncludeOriginOfCondition", "IndicatorLED", "indices", "InfiniBand", "IOV",
                       "iQN", "iSCSI", "iWARP", "JEDEC", "JEP", "JSON", "keepalive", "Kerberos", "keytab", "kilopascal", "KMIP", "KVM", "KVMIP", "LastState", "LBA", "LDAP", "LLDP", "locator",
                       "LogEntry", "LogService", "LongDescription", "loopback", "LUN", "ManagerAccount", "maskable", "MaxOccurrences", "Mbit", "mebibytes", "MemorySummary",
                       "MessageArg", "MessageArgs",  "MessageId", "MessageIds", "MessageRegistry", "metadata", "MetricReports", "MetricReportDefinitionType", "MetricValue", "MiB",
                       "Microcontroller", "MTU",  "Multibit", "multicast", "multihoming", "multihop", "Multipart", "MultiProtocol", "namespace", "namespaces", "NAK", "NAND",
                       "NavigationProperties", "NDP", "NEMA",  "NetBIOS", "netmask", "NetworkAdapter", "NGUID", "NIC", "NICs", "NIST", "NQN", "NMI", "NotRedundant", "NSID", "NTP",
                       "NVDIMM", "NVDIMMs", "NVM", "NVMe", "NVN", "nullable", "NXP", "OCSP", "OData", "offline", "Oem", "online", "OnStartUpdateRequest", "OpenAPI",
                       "OperationApplyTime", "Optane", "OriginOfCondition",  "OriginOfCondition's", "overprovision", "OSI", "passphrase", "passphrases", "passthrough", "PCI",
                       "PCIe", "PDU", "pinout", "PEM", "phy", "PLA", "PLDM", "PowerISA", "PPIN", 
                       "PrivilegeType", "ProcessorSummary", "PushPowerButton", "PXE", "QuickPath", "quiescing", "RackUnit", "RDIMM", "RDMA", "RDP", "ReadingType",
                       "RecurrenceInterval", "Redfish",  "RedfishMetricReport", "Referenceable", "regex", "RegistryPrefix", "RegistryPrefixes", "rekeyed", "RELP", "ReportActions",
                       "Requestor", "ResourceStatusChangedCritical", "ResourceType", "ResourceTypes", "Retransfer", "RevisionKind", "roadmap", "RoleId", "sanitization", "SAS", "schemas", "SCL",
                       "SCP", "SDA", "SDRAM", "SecurityPolicy", "SEL", "ServiceLabel", "SettingsApplyTime", "SEV", "SFF", "SFP", "SFTP", "SGRAM", "SHA", "signalling", "SLAAC", "SmartNIC", "SMB", "SMBIOS", "SNIA",
                       "SNMP", "SKU", "SoftwareInventory", "SSDP", "SSL", "StandbySpare",  "stateful", "StartUpdate", "StorageController", "StoragePool", "StoragePools", "StorageServer", "SubModel",
                       "SubSystem", "syslog", "syslogd", "TCG", "TCM", "TDP", "TLB",
                       "Telecom", "TFTP", "THD", "timestamp", "TLP", "TLS", "TPM", "TriggerActions", "UCUM", "UDIMM", "UDP", "UEFI", "UHCI", "UI", "uri", "URIs", "UltraPath",
                       "unhalted", "unicast", "unversioned", "USB", "username", "UTC", "UUID", "ValueName", "VCAT", "virtualization", "VEPA", "versioned", "VLAN", "VLANEnabled",
                       "VLANId", "VNC", "VolumeCollection", "VPD", "WMI", "WoL", "WWN", "www", "wildcard", "wildcards", "XON", "XOFF", "XPoint"];

//These are words we only want to allow for certain files
const PerFileAllowList = {
    'AccountService_v1.xml': [
        'TACACS',
        'OAuth',
        'jwks',
        'PasswordExpiration'
    ],
    'Bios_v1.xml': [
        'AdminPassword',
        'UserPassword'
    ],
    'Certificate_v1.xml': [
        'ALG',
        'challengePassword',
        'commonName',
        'subjectAltName',
        'organizationName',
        'organizationalUnitName',
        'localityName',
        'stateOrProvinceName',
        'countryName',
        'emailAddress',
        'givenName',
        'challengePassword',
        'unstructuredName',
        'domainComponent',
        'serialNumber',
        'signatureAlgorithm',
        'OID'
    ],
    'CertificateService_v1.xml': [
        'ALG',
        'challengePassword',
        'commonName',
        'subjectAltName',
        'organizationName',
        'organizationalUnitName',
        'localityName',
        'stateOrProvinceName',
        'countryName',
        'emailAddress',
        'givenName',
        'challengePassword',
        'unstructuredName',
        'domainComponent',
        'serialNumber',
        'signatureAlgorithm',
        'OID'
    ],
    'Circuit_v1.xml': [
        'cordsets',
        'CurrentSensor', //The type in the CSDL is accidentally named CurrentSensors...
        'de', //de-rated is allowed and for whatever reason adding that to the dictionary doesn't work
        'EnergySensor', //The type in the CSDL is accidentally named EnergySensors...
        'poly', //poly-phase
        'PowerSensor', //The type in the CSDL is accidentally named PowerSensors...
        'subfeed',
        'VoltageSensor' //The type in the CSDL is accidentally named VoltageSensors...
    ],
    'ContosoExtensions_v1.xml': [
        'Turboencabulator'
    ],
    'ComputerSystem_v1.xml': [
        'AutomaticRetry',
        'dmidecode',
        'EXecution',
        'Pre',
        'TrustedModule', //The type in the CSDL is accidentally named TrustedModules...
        'xxxx',
        'xxxxxxxx',
        'xxxxxxxxxxxx'
    ],
    'EventDestination_v1.xml': [
        'rsyslog'
    ],
    'EventService_v1.xml': [
        'AUTH'
    ],
    'ExternalAccountProvider_v1.xml': [
        'TACACS',
        'OAuth',
        'jwks'
    ],
    'FabricAdapter_v1.xml': [
        'REQ',
        'RSP'
    ],
    'LogEntry_v1.xml': [
        'xX', 
        'fA',
        'NN',
        'aa',
        'bb',
        'EventDir',
        'Pre'
    ],
    'LogService_v1.xml': [
        'Pre'
    ],
    'ManagerNetworkProtocol_v1.xml': [
        'snmpEngineID'
    ],
    'Memory_v1.xml': [
        'FB'
    ],
    'Outlet_v1.xml': [
        'CurrentSensor', //The type in the CSDL is accidentally named CurrentSensors...
        'de', //de-rated is allowed and for whatever reason adding that to the dictionary doesn't work
        'poly', //poly-phase
        'Schuko',
        'VoltageSensor' //The type in the CSDL is accidentally named VoltageSensors...
    ],
    'Protocol_v1.xml': [
        'FIbre',
        'CONnection'
    ],
    'PortMetrics_v1.xml': [
        'ECRC',
        'LLR',
        'PCRC'
    ],
    'PowerDistribution_v1.xml': [
        'subfeed'
    ],
    'RedfishExtensions_v1.xml': [
        'Un',
        'un'
    ],
    'Resource_v1.xml': [
        'ADDCODE',
        'BLD',
        'chou',
        'FLR',
        'FS',
        'HNO',
        'HNS',
        'LMK',
        'LOC',
        'PCN',
        'Platz',
        'PLC',
        'PNC',
        'POBOX',
        'POM',
        'PRD',
        'pre',
        'PRM',
        'nn',
        'nnnnn',
        'nnnnnn',
        'RDBR',
        'RDSEC',
        'RDSUBBR',
        'shi',
        'STS'
    ],
    'Schedule_v1.xml': [
        'OrgID',
        'ScheduleName',
        'FirstTuesday'
    ],
    'SecureBootDatabase_v1.xml': [
        'KEK',
        'dbx',
        'dbr',
        'dbt',
        'PKDefault',
        'KEKDefault',
        'dbDefault',
        'dbxDefault',
        'dbrDefault',
        'dbtDefault'
    ],
    'Sensor_v1.xml': [
        'Cel',
        'cft',
        'kilopascal',
        'kPa',
        'kVAh',
        'kVARh',
        'ResetStatistics', //This was renamed and should only be in this file once
        'VAC',
        'VDC',
        'Wh'
    ],
    'Signature_v1.xml': [
        'SignatureData' //From UEFI spec
    ],
    'StorageController_v1.xml': [
        'admin',
        'oF'
    ],
    'TaskService_v1.xml': [
        'TaskState'
    ],
    'TurboencabulatorService_v1.xml': [
        'turboencabulator'
    ],
    'Volume_v1.xml': [
        'ACWU',
        'AWUN',
        'AWUPF',
        'NACWU',
        'NAWUN',
        'NAWUPF',
        'NPDA',
        'NPDG',
        'NPWA',
        'NPWG',
        'pre'
    ]
}

WordAllowList.forEach((word) => {
    SpellChecker.add(word);
});

var gSpellErrorCount = 0;
var gWordMap = {};

var args = process.argv.slice(2);

const files = glob.sync(config.get('Redfish.CSDLFilePath'));
let publishedSchemas = {};
let overrideCSDLs = [];
let promise = csdlTestSetup();
promise.then((res) => {
  publishedSchemas = res[0];
  overrideCSDLs = res.slice(1);
  let promises = [];

  files.forEach((file) => {
    let fileName = file.substring(file.lastIndexOf('/')+1);
    promises.push(new Promise((resolve, reject) => {
        CSDL.parseMetadataFile(file, options, (err, data) => {
            if(err) {
                reject(err);
            }
            descriptionSpellCheck(data, fileName);
            resolve(true);
        });
    }));
  });
  Promise.allSettled(promises).then(() => {
    console.log("Found "+gSpellErrorCount+" possible spelling errors in "+files.length+" files.");
    if(args.includes("-map")) {
        var sortable = [];
        for (var word in gWordMap) {
            sortable.push([word, gWordMap[word]]);
        }
        sortable.sort(function(a, b) {
            return b[1] - a[1];
        });
        sortable.forEach((data) => {
            console.log(data[0]+": "+data[1]);
        });
    }
  });
}).catch((err) => {
  console.log(err.message, err.stack);
  process.exit(1)
});


function csdlTestSetup() {
    let arr = [];
    OverRideFiles.forEach((file) => {
      arr.push(new Promise((resolve, reject) => {
        CSDL.parseMetadataUri(file, options, (err, csdl) => {
          if(err) {
            reject(err);
            return;
          }
          assert.notEqual(csdl, null);
          resolve(csdl);
        });
      }));
    });
    return Promise.all(arr);
}

function descriptionSpellCheck(csdl, file) {
    let long_descriptions = CSDL.search(csdl, 'Annotation', 'OData.LongDescription');
    let descriptions = CSDL.search(csdl, 'Annotation', 'OData.Description');
    if(long_descriptions.length !== 0) {
      for(let i = 0; i < long_descriptions.length; i++) {
        let str = long_descriptions[i].String;
        stringSpellCheck(str, file, csdl);
      }
    }
    if(descriptions.length !== 0) {
        for(let i = 0; i < descriptions.length; i++) {
          let str = descriptions[i].String;
          stringSpellCheck(str, file, csdl);
        }
      }
}

function typeExistsWithName(name, badStr, csdl) {
    let props = CSDL.search(csdl, name);
    for(let j = 0; j < props.length; j++) {
        if(props[j].Name === badStr) {
            return true;
        }
    }
    return false;
}

function stringSpellCheck(str, file, csdl) {
    let errs = SpellChecker.checkSpelling(str);
    if(errs.length === 0) {
        return;
    }
    errStrings = "";
    for(let i = 0; i < errs.length; i++) {
        //skip URIs
        if(errs[i].start > 1 && str.substring(errs[i].start-1, errs[i].start) === "/") {
            continue;
        }
        //Skip annotations
        if(errs[i].start > 1 && str.substring(errs[i].start-1, errs[i].start) === "@") {
            continue;
        }
        //Skip type names
        if(errs[i].start > 8 && str.substring(errs[i].start-8, errs[i].start) === "of type ") {
            continue;
        }
        badStr = str.substring(errs[i].start, errs[i].end);
        //Skip this type name as well
        if(file.startsWith(badStr)) {
            continue;
        }
        let found = typeExistsWithName('Property', badStr, csdl);
        if(!found) {
            found = typeExistsWithName('NavigationProperty', badStr, csdl);
        }
        if(!found) {
            found = typeExistsWithName('EntityType', badStr, csdl);
        }
        if(!found) {
            found = typeExistsWithName('ComplexType', badStr, csdl);
        }
        if(!found) {
            found = typeExistsWithName('TypeDefinition', badStr, csdl);
        }
        if(!found) {
            let props = CSDL.search(csdl, 'EnumType');
            for(let j = 0; j < props.length; j++) {
                if(props[j].Name === badStr) {
                    found = true;
                    break;
                }
                //Also search the members...
                if(props[j].Members[badStr] !== undefined) {
                    found = true;
                    break;
                }
            }
        }
        if(!found) {
            found = typeExistsWithName('Action', badStr, csdl);
        }
        if(!found) {
            found = typeExistsWithName('Singleton', badStr, csdl);
        }
        if(!found) {
            found = typeExistsWithName('Term', badStr, csdl);
        }
        if(!found) {
            found = typeExistsWithName('Parameter', badStr, csdl);
        }
        if(!found) {
            let props = CSDL.search(csdl, 'Reference', undefined, true);
            for(let j = 0; j < props.length; j++) {
                if(props[j].Includes[badStr] !== undefined) {
                    found = true;
                    break;
                }
            }
        }
        //Skip words that are also property names
        if(found) {
            continue;
        }
        if(PerFileAllowList[file] !== undefined) {
            let list = PerFileAllowList[file];
            if(list.includes(badStr)) {
                continue;
            }
        }
        errStrings += badStr;
        errStrings += " ";
        gSpellErrorCount++;
        if(args.includes("-map")) {
            if(gWordMap[badStr] === undefined) {
                gWordMap[badStr] = 1;
            } else {
                gWordMap[badStr]++;
            }
        }
    }
    if(errStrings === "") {
        return;
    }
    console.log(file+": Mispelled words: "+errStrings);
}