###############################################################################
#
# File:      run_prod.sh
# Author(s): Nico
# Scope:     Run project in production mode
#
# Created:   07 February 2024
#
###############################################################################
export PYTHONPATH="$PWD"

if [ ! -d "venv" ]; then
  echo "Virtualenv (venv) not found in ${DIR}"
  echo "Installing virtualenv in ${DIR}/venv ..."
  python3.11 -m venv venv
fi
source venv/bin/activate
echo "Checking venv..."
pip install -U pip
pip install -r requirements.txt
echo "DONE!"
echo "Running main.py script - prod mode (API port 8000)"
nohup python main.py -p 8000 -l guysvintedbot_prod.log &
