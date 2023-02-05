#!/bin/bash
# Update mlocate databases in specific locations
# BRL XPS8500

# TODO: make script iterate over text file rather than separate commands
# TODO: |/data/path|/idx/path|idx_name|[/prune/paths]|[--opts]

echo 'script begin'

echo 'updating 6 databases'

echo '1 default'
# default path: /var/lib/mlocate/mlocate.db
if [ -f /var/lib/mlocate/mlocate.db ]; then
    updatedb -l 0 -U / -o /var/lib/mlocate/mlocate.db
fi

echo '2 brl'
if [ -f ~/locate-brl.db ]; then
    updatedb -l 0 -U ~ -o ~/locate-brl.db
fi

echo '3 root (excluding /mnt)'
if [ -f /locate.db ]; then
    updatedb -l 0 -U / -o /locate.db --prunepaths /mnt
fi

echo '4 /mnt/c'
if [ -f /mnt/c/locate-c.db ]; then
    updatedb -l 0 -U /mnt/c -o /mnt/c/locate-c.db
fi

echo '5 /mnt/d'
if [ -f /mnt/d/locate-d.db ]; then
    updatedb -l 0 -U /mnt/d -o /mnt/d/locate-d.db
fi

echo '6 /mnt/e'
if [ -f /mnt/e/locate-e.db ]; then
    updatedb -l 0 -U /mnt/e -o /mnt/e/locate-e.db
fi

echo 'script complete'
# END

