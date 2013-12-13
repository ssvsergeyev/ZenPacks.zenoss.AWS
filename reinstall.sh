set -x

zenpack --remove ZenPacks.zenoss.AWS
zenpack --link --install .

zopectl restart
zenhub restart

zenbatchload ~/aws_batchload.txt
zenmodeler run --device=bunyk

set +x
