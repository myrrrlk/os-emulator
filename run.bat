@echo off
pushd "%~dp0"
python -m src.main %*
popd