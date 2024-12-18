###############################################################################
#
# File:      rsync_nico.sh
# Author(s): Nico
# Scope:     Send the project in nico's test folder
#
# Created:   07 February 2024
#
###############################################################################

branch=$(git rev-parse --abbrev-ref HEAD)

if [[ ! "$branch" =~ ^(dev|main)$ ]]; then
    rsync -e "ssh" --exclude=".idea/" --exclude='.git/' --exclude="__pycache__/" \
    --exclude="/venv" --exclude="*.csv" --exclude="*.log" --exclude=".gitignore" \
    -rav . guys@guysmachine:/home/guys/guysvintedbot/tests/nico
else
    echo "Branch is dev or main. Skipping rsync command."
fi
