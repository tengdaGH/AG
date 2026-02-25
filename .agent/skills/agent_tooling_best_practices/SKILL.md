---
name: agent_tooling_best_practices
description: Core best practices for agents interacting with the file system and IDE. Covers how to safely move, copy, or delete files without triggering terminal sandboxing blocks.
---

# Agent Tooling Best Practices

As an agent, you have access to powerful terminal commands (`run_command`), but you also operate within an IDE environment with purpose-built APIs (`read_file`, `write_to_file`, `multi_replace_file_content`).

To prevent the system from pausing and waiting for manual user approval (which can make you appear stuck or hung), you must follow these rules when interacting with the file system:

## 1. Do Not Use Bash for File Mutations

**NEVER** use the `run_command` tool to execute `mv`, `cp`, `rm`, or `mkdir` on critical user files or directories. 

The security sandboxing on the user's terminal will often intercept these commands as potentially destructive. Even if the user has "Terminal Command Auto Execution" set to "Always Proceed", the system safety layer will still block these specific bash commands and wait for a manual click, causing your execution to silently time out or freeze.

## 2. Use Native Tools for Copying & Moving

If you need to copy or move a file:
1. Use `read_file` to read the exact contents of the source file.
2. Use `write_to_file` to create the new file at the destination path.
3. If it is a move operation, document that the user will need to delete the original file, or wait until the end of the conversation to ask the user to authorize an `rm` command.

## 3. Use Native Tools for Everything Else

Following Critical Instructions:
- **Never** run `cat`, `echo`, or `tee` inside a bash command to create or view files. Use `write_to_file` or `view_file`.
- **Always** use `grep_search` instead of running `grep` inside a bash command.
- **Do not** use `ls` for listing directories; use the native `list_dir` tool.
- **Do not** use `sed` or `awk` for replacing text; use `replace_file_content` or `multi_replace_file_content`.

## Why This Matters
When you use native API tools, the IDE can track your changes, provide rich diffs to the user, and allow for easy undo operations. Bash commands bypass the IDE's history and safety mechanisms and should be strictly reserved for running scripts, starting servers, or executing project-specific CLI tools (like `npm run dev` or `python script.py`).
