# MySQL Replication Runbook

This runbook provides a step-by-step guide to configure MySQL replication between a master node and a slave node. Replication allows the slave to maintain an identical copy of the master’s databases by continuously applying changes recorded in the master’s binary logs. This setup is useful for load balancing, backups, or high availability. The process involves configuring the master, creating a replication user, taking a database snapshot, and setting up the slave to follow the master.

## On the Master Node

### 1. Configure the Master Server with `server-id = 1`

To enable replication, the master node must be uniquely identifiable and configured to log all changes to its databases. This is done by setting a `server-id` and enabling binary logging.

- **Locate the Configuration File**: The MySQL configuration file is typically found at `/etc/mysql/mysql.conf.d/mysqld.cnf`. This file controls the MySQL server settings.
- **Edit the File**: Open the file with a text editor (e.g., `nano`) using superuser privileges:
  ```shell
  sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf
  ```
- **Add or Modify Settings**: Under the [mysqld] section, ensure the following lines are present. If they already exist, update them:
   
   ```sql
   [mysqld]
   server-id=1              # Unique identifier for the master node (must differ from the slave).
   log-bin=mysql-bin        # Enables binary logging, which records all database changes.
   bind-address=0.0.0.0     # Allows connections from any IP (required for replication over a network).
   ```

   - **server-id**: A unique number for this MySQL instance (e.g., 1 for the master).
   - **log-bin**: Specifies the base name for binary log files (e.g., mysql-bin.000001).
   - **bind-address**: Set to 0.0.0.0 to allow external connections from the slave.

- **Save and Exit**: Save the file (Ctrl+O, Enter, Ctrl+X in nano).
- **Restart MySQL**: Apply the changes by restarting the MySQL service:
  ```shell
  sudo systemctl restart mysql
  ```
- **Verify**: Ensure the service is running with sudo systemctl status mysql.

### 2. Create a Replication User
The slave needs a dedicated MySQL user account with replication privileges to connect to the master and fetch updates.

- **Log in to MySQL**: Access the MySQL shell as the root user:
  ```shell
  mysql -u root -p
  ```
  - **-u root -p**: Connects as the root user (prompts for password).
  Enter the root password when prompted.

- **Create the User**: Execute the following SQL commands:
  ```sql
  CREATE USER 'replica_user_impulsos'@'%' IDENTIFIED BY 'ReplicaImpulsosMySQLPass';
  GRANT REPLICATION SLAVE ON *.* TO 'replica_user_impulsos'@'%';
  FLUSH PRIVILEGES;
  ```
  - **CREATE USER**: Defines a new user replica_user_impulsos with the password ReplicaImpulsosMySQLPass. The '%' wildcard allows connections from any host.
  - **GRANT REPLICATION SLAVE**: Grants the user permission to replicate data from the master.
  - **FLUSH PRIVILEGES**: Ensures the changes take effect immediately.

- **Exit**: Type ```EXIT;``` to leave the MySQL shell.

### 3. Lock the Master for a Snapshot
To ensure data consistency during the backup, temporarily prevent changes to the master’s databases by locking all tables.

- **Log in to MySQL**: Use a user with sufficient privileges (e.g., impulsos):
  ```shell
  mysql -u root -p
  ```
- **Lock Tables**: Run the following command:
  ```sql
  FLUSH TABLES WITH READ LOCK;
  ```
  - This command flushes any pending writes to disk and locks all tables in a read-only state. It ensures the database remains static while you take a snapshot.

### 4. Retrieve the Master’s Replication Status
The master’s binary log file and position are critical for the slave to know where to start replicating.
- **Check Status**: In the MySQL shell, run:
  ```sql
  SHOW MASTER STATUS;
  ```
- **Sample Ouput**:
  ```sql
  mysql> SHOW MASTER STATUS;
  +------------------+----------+--------------+------------------+-------------------+
  | File             | Position | Binlog_Do_DB | Binlog_Ignore_DB | Executed_Gtid_Set |
  +------------------+----------+--------------+------------------+-------------------+
  | mysql-bin.000001 |      890 |              |                  |                   |
  +------------------+----------+--------------+------------------+-------------------+
  1 row in set (0.00 sec)
  ```
- **Record Details**: Note the File (e.g., mysql-bin.000001) and Position (e.g., 890). These values indicate the exact point in the binary log where the slave should begin replication.

### 5. Export the Master Database
Create a backup of all databases, including the replication log position, to initialize the slave.
- **Run mysqldump**: Execute this command in the terminal (not the MySQL shell):
  ```shell
  mysqldump -u root -p --all-databases --master-data > db_impulsos_backup.sql
  ```
  - **--all-databases**: Includes all databases in the backup.
  - **--master-data**: Embeds the SHOW MASTER STATUS information (log file and position) in the dump file.
  - **> db_impulsos_backup.sql**: Saves the output to a file named db_impulsos_backup.sql.

- **Verify**: Check that the file exists (e.g., ls -lh db_impulsos_backup.sql).

### 6. Unlock the Master’s Tables
Release the read lock to allow normal operations to resume on the master.
- **Log in to MySQL**: If not already connected:
  ```shell
  mysql -u impulsos -p
  ```
- **Unlock Tables**: Run:
  ```sql
  UNLOCK TABLES;
  ```

## On the Slave Node
### 1. Import the Master’s Database Dump
Transfer the backup file from the master to the slave and restore it to synchronize the initial state.
- **Transfer the File**: Use rsync or scp to copy db_impulsos_backup.sql to the slave:
  - Using ```rsync``` (preserves file attributes):
  ```shell
  rsync -a /path/to/backup/db_impulsos_backup.sql user@slave_ip:/path/to/backup/
  ```
  - Using ```scp``` (simple copy):
  ```shell
  scp /path/to/backup/db_impulsos_backup.sql user@slave_ip:/path/to/backup/
  ```
  - Replace ```user``` with the SSH username and ```slave_ip``` with the slave’s IP address. Remember that we are working with root user.
- **Import the Dump**: On the slave, load the backup into MySQL:
  ```shell
  mysql -u root -p < /path/to/backup/db_impulsos_backup.sql
  ```
  - This restores all databases and sets the replication starting point.

### 2. Configure the Slave Server with server-id = 2
Like the master, the slave needs a unique server-id and proper configuration.
- **Edit the Configuration File**: Open /etc/mysql/mysql.conf.d/mysqld.cnf:
  ```shell
  sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf
  ```
- **Add or Modify Settings**: Ensure these lines are present under [mysqld]:
  ```sql
  [mysqld]
  server-id=2              # Unique ID for the slave (different from the master).
  log-bin=mysql-bin        # Optional: Enables binary logging on the slave (useful if it becomes a master later).
  bind-address=0.0.0.0     # Allows network connections.
  ```
- **Restart MySQL**: Apply the changes:
  ```shell
  sudo systemctl restart mysql
  ```
### 3. Configure Replication Parameters
Tell the slave how to connect to the master and where to start replicating.
- **Log in to MySQL**: On the slave:
  ```shell
  mysql -u root -p
  ```
- **Set Replication**: Use the values from the master’s ```SHOW MASTER STATUS```:
  ```sql
  CHANGE MASTER TO
    MASTER_HOST='68.183.100.232',                # Master’s IP address.
    MASTER_USER='replica_user_impulsos',         # Replication user created on the master.
    MASTER_PASSWORD='ReplicaImpulsosMySQLPass',  # Password for the replication user.
    MASTER_LOG_FILE='mysql-bin.000001',          # Log file from SHOW MASTER STATUS.
    MASTER_LOG_POS=890,                          # Position from SHOW MASTER STATUS.
    MASTER_SSL=1,                                # Enables SSL for secure replication.
    MASTER_SSL_CA='/var/lib/mysql/ca.pem';       # Path to the CA certificate for SSL.
  ```
    - Adjust MASTER_HOST, MASTER_LOG_FILE, and MASTER_LOG_POS based on your setup. Use data of "SHOW MASTER STATUS" of master to configure.

### 4. Start the Replication Process
Begin replication on the slave.
- **Start Slave**: In the MySQL shell:
  ```sql
  START SLAVE;
  ```
  - This initiates the replication threads: one for I/O (fetching logs) and one for SQL (applying changes).

### 5. Verify Replication Status
Confirm that replication is working correctly.
- **Check Status**: Run:
  ```sql
  SHOW SLAVE STATUS\G
  ```
  - The ```\G``` formats the output vertically for readability.

- **Key Indicators**: Look for these values:
  ```text
  Slave_IO_Running: Yes       # Indicates the I/O thread is connected to the master.
  Slave_SQL_Running: Yes      # Indicates the SQL thread is applying changes.
  ```
  - If either is No, check ```Last_IO_Error``` or ```Last_SQL_Error``` in the output for troubleshooting.


## Additional Considerations

- **SSH Connectivity**: Both the master and slave must have passwordless SSH configured (e.g., using SSH keys) for secure file transfers. Test with ssh user@slave_ip from the master.
- **SSL Certificates**: For MASTER_SSL=1, both nodes must use certificates signed by the same Certificate Authority (CA). Ensure /var/lib/mysql/ca.pem exists and matches on both machines.
- **Network**: Verify that the master’s IP (e.g., 68.183.100.232) is reachable from the slave and that port 3306 (MySQL default) is open.

## Troubleshooting and Reactivating MySQL Replication

If you notice that the slave database is no longer replicating after some time, it means that the slave has lost synchronization with the master. This can occur due to several reasons:

- Network Issues: The slave couldn’t connect to the master (e.g., network outage or firewall blocking port 3306).
- Replication Errors: The slave encountered an error while applying changes (e.g., duplicate key errors, schema mismatches).
- Master Log Purge: The master deleted binary logs that the slave hadn’t yet processed.
- Manual Intervention: Someone stopped the slave replication process (```STOP SLAVE;```).

You can check the replication status with:
  ```sql
  SHOW SLAVE STATUS\G
  ```
Look for:

- **Slave_IO_Running**: No (I/O thread stopped, meaning it can’t fetch logs from the master).
- **Slave_SQL_Running**: No (SQL thread stopped, meaning it can’t apply logs).
- ```Last_IO_Error``` or ```Last_SQL_Error``` (specific error messages).

### 1. First Restart Slave and Verify
Some time, only it is necessary restart replication to reactivate replication.
```shell
mysql -u root -p
```
```sql
STOP SLAVE;
START SLAVE;
SHOW SLAVE STATUS\G
```
### 2.  Reactivate Replication Without Damaging the Slave
To restore replication, you need to identify the issue, fix it, and resync if necessary. Below is a detailed procedure to troubleshoot and reactivate replication safely.

If the slave database stops replicating, follow these steps to diagnose the issue and restore replication without damaging the slave. This process ensures the slave remains consistent with the master.

#### 1. Check the Slave Status
Determine why replication stopped by inspecting the slave’s status.

- **Run the status command**:
  ```shell
  mysql -u root -p
  ```
  ```sql
  SHOW SLAVE STATUS\G
  ```
- **Key Fields to Check**:
    - ```Slave_IO_Running```: Should be Yes. If No, the slave can’t connect to the master.
    - ```Slave_SQL_Running```: Should be Yes. If No, there’s an error applying changes.
    - ```Last_IO_Error```: Details connection or log retrieval issues.
    - ```Last_SQL_Error```: Details errors in applying the master’s changes.
    - ```*Master_Log_File``` and Read_Master_Log_Pos: The last log file and position the slave processed.
    - ```Relay_Log_File``` and ```Relay_Log_Pos```: The last relay log position applied.

- **Common Issues**:

    - **Network Failure**: Check connectivity to the master (```ping <master_ip>``` or ```telnet <master_ip> 3306```).
    - **SQL Error**: Look at ```Last_SQL_Error``` (e.g., "duplicate entry" or "table doesn’t exist").
    - **Log Missing**: The master purged logs before the slave processed them (```Read_Master_Log_Pos``` points to a non-existent file).

#### 2. Stop the Slave Replication
Pause replication to prevent further errors while troubleshooting.
- **Stop Slave**:
  ```shell
  mysql -u root -p
  ```
  ```sql
  STOP SLAVE;
  ```

#### 3. Fix the Root Cause
Address the specific issue identified in Step 1.
- If ```Slave_IO_Running: No```:
  - Verify the master is reachable and the IP/port are correct (MASTER_HOST in CHANGE MASTER TO).
  - Check the replication user credentials (MASTER_USER, MASTER_PASSWORD).
  - Ensure the master’s binary logs still exist:
    ```shell
    mysql -u root -p -h <master_ip>
    ```
    ```sql
    SHOW BINARY LOGS;
    ```
    Compare with Master_Log_File from the slave. If the file is missing, proceed to resync (Step 5).
- If ```Slave_SQL_Running: No```:
  - Read ```Last_SQL_Error```. Common fixes:
    - **Duplicate Key**: Skip the problematic transaction:
    ```sql
    SET GLOBAL sql_slave_skip_counter = 1;
    START SLAVE;
    ```
    Repeat until ```Slave_SQL_Running``` is Yes, but use cautiously as this skips data.
    - **Schema Mismatch**: Manually align the slave’s schema with the master’s (e.g., create missing tables).
    ```sql
    START SLAVE;
    SHOW SLAVE STATUS\G
    ```
#### 4. Restart Replication (If No Resync Needed)
If the issue is resolved (e.g., network restored or error skipped), try restarting replication.
```shell
mysql -u root -p
```
```sql
STOP SLAVE;
START SLAVE;
SHOW SLAVE STATUS\G
```
Ensure ```Slave_IO_Running``` and ```Slave_SQL_Running``` are both Yes. If not, proceed to resync.

## Important Notes
- **Avoid manual inserts**: manually adding data to the slave can break replication. Only do this if you plan to resync afterwards.
- **Take a backup before resyncing**: always backup the current state of the slave before importing a new dump, in case of errors.
- **Monitor periodically**: after reactivating, periodically check SHOW SLAVE STATUS\G to make sure replication remains active.
- **Resync the slave (if missing logs or errors persist)**: in this case, the most efficient thing to do is to recreate the replica.