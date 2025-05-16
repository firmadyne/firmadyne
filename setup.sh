#!/bin/bash
set -e
set -x

# Update package lists
sudo apt update
sudo apt upgrade
# Install required packages with -y flag
sudo apt-get install -y busybox-static fakeroot git dmsetup kpartx netcat-openbsd nmap snmp \
    python3-psycopg2 uml-utilities util-linux vlan python3-pip python3-magic

# Set python3 as default python
sudo update-alternatives --install /usr/bin/python python /usr/bin/python3 10

# Clone firmadyne
git clone --recursive https://github.com/firmadyne/firmadyne.git

# Create and Move to firmadyne directory, push the current directory into stack
pushd firmadyne

sudo apt install -y curl

# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source "$HOME/.cargo/env"

# Clone and build binwalk
git clone https://github.com/ReFirmLabs/binwalk
sudo ./binwalk/dependencies/ubuntu.sh
pushd binwalk
cargo build --release
popd
popd
# Install and configure PostgreSQL
sudo apt-get install -y postgresql

# # Create firmadyne user and database
# echo "Creating PostgreSQL user and database..."
# sudo -u postgres createuser -P firmadyne
# sudo -u postgres createdb -O firmadyne firmware

# Create firmadyne user and database
echo "Creating PostgreSQL user and database..."

# Check if the 'firmadyne' user exists
USER_EXISTS=$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='firmadyne'")
if [ "$USER_EXISTS" != "1" ]; then
    echo "Creating user 'firmadyne'..."
    sudo -u postgres createuser -P firmadyne
else
    echo "User 'firmadyne' already exists, skipping..."
fi

# Check if the 'firmware' database exists
DB_EXISTS=$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='firmware'")
if [ "$DB_EXISTS" != "1" ]; then
    echo "Creating database 'firmware'..."
    sudo -u postgres createdb -O firmadyne firmware
else
    echo "Database 'firmware' already exists, skipping..."
fi

# Import schema
sudo -u postgres psql -d firmware < ./firmadyne/database/schema

# Download firmadyne binaries
pushd firmadyne
sudo apt-get install binwalk
sudo apt-get install tkinterdnd2
sudo apt update && sudo apt install -y python3 python3-pip python3-tk pexpect
./download.sh
popd

# Install QEMU packages
sudo apt-get install -y qemu-system-arm qemu-system-mips qemu-system-x86 qemu-utils
# SetUp Environment configurations
#FIRMADYNE_DIR="$(pwd)/firmadyne"
#echo "DIR=$(pwd)" > "${FIRMADYNE_DIR}/.env"
echo ""
echo "Installation completed successfully!"
echo "You may need to run 'source ~/.cargo/env' or restart your shell to access rust tools."
echo "Don't forget to configure your firmadyne.config with the database credentials."
# Set FIRMWARE_DIR in firmadyne.config
# Sets up Environment Variable FIRMADYNE as $"pwd", then appends it as first line in firmadyne.config
mv firmadyne.config firmadyne.config.orig
echo -e '#!/bin/sh' "\nFIRMWARE_DIR=$(pwd)/" > firmadyne.config
cat firmadyne.config.orig >> firmadyne.config
