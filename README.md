# dotfiles

brl0 dotfiles

## TODO

- fix shopts
- fix install_dots2
- root level file linking?
- cleanup autorun logic

## Issues

- bash: shopt: .files/scripts/set_shopts.sh: invalid shell option name
- bash: shopt: .files/scripts/sourcing.sh: invalid shell option name
- file /home/ubuntu/.env does not exist
- file /home/ubuntu/.config/asdf-direnv/bashrc does not exist
- file /home/ubuntu/.bash.d/cht.sh does not exist
- file /home/ubuntu/google-cloud-sdk/path.bash.inc does not exist
- file /home/ubuntu/google-cloud-sdk/completion.bash.inc does not exist
- bash: register-python-argcomplete: command not found
- bash: /home/ubuntu/scripts/fix_path.py: No such file or directory

## Roadmap

- script to add files

## Notes

/etc/apt/apt.conf.d/99-Phased-Updates

```bash
Update-Manager::Always-Include-Phased-Updates true;
APT::Get::Always-Include-Phased-Updates true;
```
