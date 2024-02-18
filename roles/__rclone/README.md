# Set up rclone on host

Install and configure rclone

Load all config snippets in `rclone_local_config_dir` (default `rclone/`) to `rclone_remote_config_file_path` (default `~/.config/rclone/rclone.conf` )

If `rclone_load_group_config` is `true`, also load config snippets under `<group>` subdirectories of `rclone_local_config_dir`

Sample config snippet (more in `sample_config_dir/`):
```ini
[ExampleGoogleDriveRemote]
type = drive
client_id = 12345
client_secret = 67890
token = {"access_token":"","token_type":"","refresh_token":"","expiry":""}
```

If two config snippets have the same file name, the one loaded later (in `<group>` subdirectories) takes precedence, but there's no rule to determine which `<group>` has priority