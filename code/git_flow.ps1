<#
.SYNOPSIS
Automates a safe and repeatable Git workflow for this repository.

.DESCRIPTION
This script performs a full Git workflow with validation steps in between.
It is intended to reduce human error when committing and pushing changes.

The script executes the following steps in order:

1. Adds all modified files to the Git staging area (git add .)
2. Displays the current Git status
3. Runs Python validation tools to verify repository integrity
4. Creates a Git commit using a user-provided commit message
5. Pushes the commit to the remote repository
6. Stops immediately on any error and reports the failing step

If any step fails, the script exits with a non-zero exit code and does not
continue to the next step.

.PARAMETER CommitMessage
The commit message to use for the Git commit.
This parameter is mandatory.

.REQUIREMENTS
- Git must be installed and available in PATH
- Python must be installed and available in PATH
- Validation scripts must exist in the tools/ directory
- Script must be executed from the root of the Git repository

.EXAMPLE
.\scripts\git_flow.ps1 "Fix recipe validation and formatting"
#>


param (
    [Parameter(Mandatory=$true)]
    [string]$CommitMessage
)

function Fail($msg) {
    Write-Host "ERROR: $msg" -ForegroundColor Red
    exit 1
}

Write-Host "== Git add =="
git add .
if ($LASTEXITCODE -ne 0) { Fail "git add failed" }

Write-Host "== Git status =="
git status

Write-Host "== Running Python validations =="
python code/recipe_linter.py _recipes c:\tmp\report.md
if ($LASTEXITCODE -ne 0) { Fail "Recipe validation failed" }

# python tools/validate_structure.py
# if ($LASTEXITCODE -ne 0) { Fail "Structure validation failed" }

Write-Host "== Git commit =="
git commit -m "$CommitMessage"
if ($LASTEXITCODE -ne 0) { Fail "git commit failed (nothing to commit?)" }

Write-Host "== Git push =="
git push
if ($LASTEXITCODE -ne 0) { Fail "git push failed" }

Write-Host "SUCCESS: All steps completed" -ForegroundColor Green
