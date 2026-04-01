from __future__ import annotations

from pathlib import Path


SYSTEMD_UNIT_TEMPLATE = """[Unit]
Description=CatCam offline event capture
After=local-fs.target

[Service]
Type=simple
User={service_user}
WorkingDirectory={project_root}
Environment=PYTHONUNBUFFERED=1
ExecStart={python_bin} -m catcam.cli --config {config_path} run
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""


def render_systemd_unit(
    project_root: str | Path,
    service_user: str,
    config_path: str | Path | None = None,
) -> str:
    root = _normalize_path(project_root)
    config = _normalize_path(config_path) if config_path is not None else root / "configs" / "rpi4-prod.json"
    python_bin = root / ".venv" / "bin" / "python"
    return SYSTEMD_UNIT_TEMPLATE.format(
        service_user=service_user,
        project_root=root,
        python_bin=python_bin,
        config_path=config,
    )


def _normalize_path(path: str | Path) -> Path:
    candidate = Path(path).expanduser()
    if candidate.is_absolute():
        return candidate
    return (Path.cwd() / candidate).resolve()
