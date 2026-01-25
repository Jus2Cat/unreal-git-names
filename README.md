# Unreal Engine `One file per actor` git support

CLI tools to decode Unreal Engine 5 **OFPA (One File Per Actor)** hashed filenames into human-readable Actor Labels. 
 
## The Problem

In Unreal Engine 5, the World Partition system (One File Per Actor) saves actors in the `__ExternalActors__` folder using hashed filenames like `KCBX0GWLTFQT9RJ8M1LY8.uasset`.

This makes it impossible to identify which actors have been modified in Git without opening the Unreal Editor.


## SourceGit Integration (UI Client)

I have created a Pull Request to integrate this functionality natively into **[SourceGit PR #2068](https://github.com/sourcegit-scm/sourcegit/pull/2068)**.

You can test this feature right now!
👉 **Download the custom SourceGit build for Windows and Linux from the [Releases](../../releases) page.**

![One-file-per-actor-git-support](https://github.com/user-attachments/assets/2a9e79a9-e564-42b0-956a-72acbb193692)

## Features 

- **Zero Dependencies**: 🚀Uses standard Python library only. (Unreal Engine or any third-party plugins)
- **Fast**: ~0.09ms per file (processes 1000+ files in milliseconds).
- **Robust**: Heuristic header scanning adapts to UE `5.1`, `5.3`, `5.4`, `5.6`, `5.7` +.
- **Context Aware**: Extracts `ActorLabel` (for actors) and `FolderLabel` (for folders).

## Usage

### Single File
```bash
python scripts/get_actor_name.py path/to/OFPA.uasset
# Output: BP_PlayerCharacter
```

### Entire Folder
Scans a folder recursively and prints names for all `.uasset` files found.
```bash
python scripts/get_actor_name.py Content/__ExternalActors__
```

### Options
- `--show-path`: Print the full path alongside the decoded name.
- `--show-type`: Print the label type (`[ActorLabel]`, `[FolderLabel]`).

```bash
python scripts/get_actor_name.py folder --show-path --show-type
# Output: E:\...\KCBX0G.uasset | [ActorLabel] | BP_PlayerCharacter
```
### Example

**Before:**
```text
modified: Content/__ExternalActors__/Maps/Main/KCBX0GWLTFQT9RJ8M1LY8.uasset
```

**After (using this tool):**
```text
BP_PlayerCharacter
```

## How It Works

1.  **Heuristic Header Scan**: Locates the Name Map in the `.uasset` header, bypassing version-specific offsets.
2.  **Index Search**: Finds indices for `ActorLabel` / `FolderLabel` and `Label` in the Name Map.
3.  **Pattern Matching**: Scans the file body for the 16-byte Property Tag pattern `[Label_Index, 0, StrProperty_Index, 0]`.
4.  **Extraction**: Reads the string value immediately following the tag.

## License

ISC License. See [LICENSE](LICENSE) file for details.
