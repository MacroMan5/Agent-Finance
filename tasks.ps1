param([Parameter(Mandatory=$true)][string]$Task)

$ErrorActionPreference = "Stop"

$skill = "plugins/agent-finance/skills/excel-financial-model"
$template = "$skill/template/model_template.xlsx"

switch ($Task) {
    "build" {
        python "$skill/build_template.py"
    }
    "validate" {
        python "$skill/validate_model.py" $template
    }
    "smoke" {
        python "$skill/build_template.py"
        if ($LASTEXITCODE -eq 0) {
            python "$skill/validate_model.py" $template
        }
    }
    "clean" {
        Remove-Item -Recurse -Force "output/agent-finance" -ErrorAction SilentlyContinue
    }
    default {
        Write-Error "Unknown task: $Task. Use: build | validate | smoke | clean"
        exit 2
    }
}
