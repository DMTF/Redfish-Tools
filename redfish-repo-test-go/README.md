# redfish-repo-test-go

This Go module provides the `repotest` executable for validating Redfish-style repositories, plus a small `ucumParse` helper for building a local UCUM unit cache.

## Download

Pre-built x86_64 binaries for Linux and Windows are attached to the latest `spmf-tools` release:

<https://github.com/DMTF/Redfish-Tools/releases/latest>

Download the appropriate asset, for example `repotest-linux-x86_64`, `repotest-windows-x86_64.exe`, `ucumParse-linux-x86_64`, or `ucumParse-windows-x86_64.exe`.

On Linux (or WSL) make the binary executable after downloading:

```bash
chmod +x repotest-linux-x86_64 ucumParse-linux-x86_64
```

## Manual validation

`repotest` embeds a default `config.yaml`. If a `config.yaml` or `redfish.yaml` is present in the current working directory, a `config` subdirectory, or the directory containing the binary, it will be loaded from there instead.

### Validate an entire repository

From the repository root:

```bash
./repotest-linux-x86_64
```

The tool walks the directories and globs configured in `config.yaml`:

- `csdlDir` (default `./metadata`) – CSDL/XML schemas
- `mockupDir` (default `./mockups`) – JSON mockups
- `jsonSchemaDir` (default `./json-schema`) – JSON schemas
- `messageRegistryDir` (default `./registries`) – JSON message registries
- `markdownGlobs` (default `./*.md`, `./docs/**/*.md`) – Markdown files

Findings are reported to stdout. The executable exits `0` when no errors are found and a non-zero value otherwise.

### Validate a single file or subdirectory

Pass a path as the last positional argument:

```bash
./repotest-linux-x86_64 ./metadata/ComputerSystem_v1.xml
```

Or target a different repository root with the `-root` flag:

```bash
./repotest-linux-x86_64 -root ./some-repo
```

### Useful flags

- `-gcc` – GCC-style machine-readable output (`file:line:col: error: message`)
- `-go` – Go-style output (`file:line: message`)
- `-pedantic` – Run additional strict checks
- `-config <file>` – Load an additional config file; comma-separated for multiple files
- `-root <dir>` – Use `<dir>` as the repository root prefix
- `-workers <multiplier>` – Worker-pool CPU multiplier (default uses `NumCPU`)
- `-cpuprofile <file>` / `-memprofile <file>` – Capture Go runtime profiles

### UCUM cache helper

`ucumParse` downloads and caches UCUM unit definitions locally:

```bash
./ucumParse-linux-x86_64
```

## VS Code diagnostic task integration

You can wire `repotest` into VS Code as a build task so reported problems appear in the **Problems** panel. Create `.vscode/tasks.json` in your workspace:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Validate Redfish repo",
      "type": "shell",
      "command": "${workspaceFolder}/repotest-linux-x86_64",
      "args": ["-gcc", "--config", "redfish.yaml"],
      "options": {
        "cwd": "${workspaceFolder}"
      },
      "group": {
        "kind": "build",
        "isDefault": true
      },
      "problemMatcher": {
        "pattern": {
          "regexp": "^(.*):(\\d+):(\\d+):\\s*(error|warning):\\s*(.*)$",
          "file": 1,
          "line": 2,
          "column": 3,
          "severity": 4,
          "message": 5
        },
        "owner": "repotest"
      },
      "presentation": {
        "reveal": "always"
      }
    }
  ]
}
```

For Windows, change the command path to use the Windows binary, for example:

```json
"command": "${workspaceFolder}\\repotest-windows-x86_64.exe"
```

With this task, press `Ctrl+Shift+B` (or `Cmd+Shift+B` on macOS) to validate the workspace. Errors and warnings reported by `repotest` are parsed and linked directly to the affected files and lines.

## Configuration

See `cmd/repotest/config.yaml` and `redfish.yaml` for the default DMTF Redfish test configuration. These YAML files can be copied or edited for your own repository. `repotest` loads the embedded `config.yaml` automatically and any extra file supplied with `-config`.

For a full description of the validation checks, see [TESTS.md](TESTS.md).
