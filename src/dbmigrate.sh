#!/bin/sh

# Run following command for first time.
# ./manage.py convert_to_south account

if [ $# != 2 ]; then
  echo "Usage: $0 <env> <action>"
  echo "<env>:"
  echo "  local     - Local development environment."
  echo "  product   - Product environment."
  echo "<action>:"
  echo "  initial   - initial south, run at first time for new apps."
  echo "  convert   - convert app to use south, run for existing apps."
  echo "  migrate   - migrate table schema, run after model changed."
  echo "  fake      - fake migrate table schema, run after app converted."
  echo "  dghost    - delete ghost migration, run after app converted."
  echo "Example 1: $0 local initial"
  echo "           $0 local migrate"
  exit 1
fi

SETTINGS=settings.$1
ACTION=$2

echo "=========================================="
# 默认只对已经migrated的apps进行操作
apps=`./manage.py installed_apps -m --settings=$SETTINGS`
if [ "$ACTION" = "convert" ]; then
    # 对于convert，操作的对象为没有被托管的apps
    apps=`./manage.py installed_apps -u --settings=$SETTINGS`
elif [ "$ACTION" = "fake" ]; then
    # 对于fake，操作的对象为没有被托管的apps
    apps=`./manage.py installed_apps -u --settings=$SETTINGS`
fi

echo "installed apps : $apps"
echo "=========================================="

for app in $apps;
do
  echo "$2 ${app}..."
  if [ "$ACTION" = "initial" ]; then
    ./manage.py schemamigration $app --initial --settings=$SETTINGS
  elif [ "$ACTION" = "migrate" ]; then
    ./manage.py schemamigration $app --auto --settings=$SETTINGS
    ./manage.py migrate $app --no-initial-data --settings=$SETTINGS
  elif [ "$ACTION" = "convert" ]; then
    ./manage.py convert_to_south $app --settings=$SETTINGS
  elif [ "$ACTION" = "fake" ]; then
    ./manage.py migrate $app --settings=$SETTINGS 0001 --fake
  elif [ "$ACTION" = "dghost" ]; then
    ./manage.py migrate --delete-ghost-migrations $app --settings=$SETTINGS
  else
    echo "Unknown action"
    exit 2
  fi
  echo
done
