set -x

zenpack --remove ZenPacks.zenoss.AWS
zenpack --link --install .

zopectl restart
zenhub restart

set +x
