#pragma once

#include <mysql/mysql.h>

#include <iostream>

// Local dev defaults. Production: OCI MySQL Heatwave (same libmysqlclient protocol).
class DbConnection {
public:
    static constexpr const char* kHost = "127.0.0.1";
    static constexpr const char* kUser = "root";
    static constexpr const char* kPassword = "wtf333";
    static constexpr unsigned int kPort = 3309;

    DbConnection() : conn_(nullptr) {}

    ~DbConnection() { disconnect(); }

    DbConnection(const DbConnection&) = delete;
    DbConnection& operator=(const DbConnection&) = delete;

    bool connect(const char* database) {
        conn_ = mysql_init(nullptr);
        if (!conn_) {
            std::cerr << "mysql_init failed\n";
            return false;
        }

        if (!mysql_real_connect(conn_, kHost, kUser, kPassword, database, kPort, nullptr, 0)) {
            std::cerr << "MySQL connect failed: " << mysql_error(conn_) << '\n';
            mysql_close(conn_);
            conn_ = nullptr;
            return false;
        }

        if (mysql_query(conn_, "SET time_zone = '+00:00'")) {
            std::cerr << "MySQL SET time_zone failed: " << mysql_error(conn_) << '\n';
            mysql_close(conn_);
            conn_ = nullptr;
            return false;
        }

        return true;
    }

    void disconnect() {
        if (conn_) {
            mysql_close(conn_);
            conn_ = nullptr;
        }
    }

    MYSQL* handle() const { return conn_; }
    bool connected() const { return conn_ != nullptr; }

private:
    MYSQL* conn_;
};
