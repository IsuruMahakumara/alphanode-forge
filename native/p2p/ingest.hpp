#pragma once

#include <httplib.h>
#include <mysql/mysql.h>
#include <simdjson.h>

#include <cstring>
#include <iostream>
#include <optional>
#include <string>

struct P2POffer {
    double price = 0;
    double min_amount = 0;
    double max_amount = 0;

    bool valid() const { return price > 0; }
};

struct P2PRateRecord {
    std::string timestamp;
    int64_t unix_timestamp = 0;
    std::optional<double> best_buy_rate;
    std::optional<double> best_sell_rate;
    double buy_min = 0;
    double buy_max = 0;
    double sell_min = 0;
    double sell_max = 0;

    std::string to_jsonl() const {
        std::string json = "{\"timestamp\":\"" + timestamp +
                             "\",\"unix_timestamp\":" + std::to_string(unix_timestamp);

        if (best_buy_rate) {
            json += ",\"best_buy_rate\":" + std::to_string(*best_buy_rate);
        }
        if (best_sell_rate) {
            json += ",\"best_sell_rate\":" + std::to_string(*best_sell_rate);
        }

        json += ",\"buy_min\":" + std::to_string(buy_min) +
                ",\"buy_max\":" + std::to_string(buy_max) +
                ",\"sell_min\":" + std::to_string(sell_min) +
                ",\"sell_max\":" + std::to_string(sell_max) + "}";
        return json;
    }
};

class P2PIngest {
public:
    P2POffer fetch_best_offer(const std::string& trade_type) {
        httplib::Client cli("https://p2p.binance.com");
        cli.set_connection_timeout(5);
        cli.set_read_timeout(10);

        std::string body = R"({"asset":"USDT","fiat":"LKR","tradeType":")" + trade_type +
                           R"(","page":1,"rows":1,"payTypes":[],"merchantCheck":false})";

        auto res = cli.Post("/bapi/c2c/v2/friendly/c2c/adv/search", body, "application/json");
        if (!res || res->status != 200) {
            return {};
        }

        return parse_offer(res->body);
    }

    P2POffer parse_offer(std::string_view json) {
        P2POffer offer;

        simdjson::dom::element doc;
        if (parser_.parse(json).get(doc)) {
            return offer;
        }

        std::string_view code;
        if (doc["code"].get_string().get(code) || code != "000000") {
            return offer;
        }

        simdjson::dom::array data;
        if (doc["data"].get_array().get(data) || data.size() == 0) {
            return offer;
        }

        simdjson::dom::object adv;
        if (data.at(0)["adv"].get_object().get(adv)) {
            return offer;
        }

        if (adv["price"].get_double().get(offer.price)) {
            return offer;
        }
        if (adv["minSingleTransAmount"].get_double().get(offer.min_amount)) {
            return offer;
        }
        if (adv["maxSingleTransAmount"].get_double().get(offer.max_amount)) {
            return offer;
        }

        return offer;
    }

private:
    simdjson::dom::parser parser_;
};

class P2PRateInserter {
public:
    explicit P2PRateInserter(MYSQL* conn) : conn_(conn), stmt_(nullptr), ready_(false) {
        if (!conn_) {
            return;
        }

        if (!ensure_table()) {
            return;
        }

        stmt_ = mysql_stmt_init(conn_);
        if (!stmt_) {
            std::cerr << "mysql_stmt_init failed: " << mysql_error(conn_) << '\n';
            return;
        }

        static const char* kInsertSql = R"(
            INSERT INTO p2p_rates (
                unix_ts, recorded_at, best_buy_rate, best_sell_rate,
                buy_min, buy_max, sell_min, sell_max
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        )";

        if (mysql_stmt_prepare(stmt_, kInsertSql, static_cast<unsigned long>(strlen(kInsertSql)))) {
            std::cerr << "mysql_stmt_prepare failed: " << mysql_stmt_error(stmt_) << '\n';
            mysql_stmt_close(stmt_);
            stmt_ = nullptr;
            return;
        }

        ready_ = true;
    }

    ~P2PRateInserter() {
        if (stmt_) {
            mysql_stmt_close(stmt_);
        }
    }

    P2PRateInserter(const P2PRateInserter&) = delete;
    P2PRateInserter& operator=(const P2PRateInserter&) = delete;

    bool ready() const { return ready_; }

    bool insert(const P2PRateRecord& row) {
        if (!ready_) {
            return false;
        }

        int64_t unix_ts = row.unix_timestamp;
        std::string recorded_at = row.timestamp;

        double best_buy = row.best_buy_rate.value_or(0);
        bool buy_is_null = row.best_buy_rate ? false : true;

        double best_sell = row.best_sell_rate.value_or(0);
        bool sell_is_null = row.best_sell_rate ? false : true;

        double buy_min = row.buy_min;
        double buy_max = row.buy_max;
        double sell_min = row.sell_min;
        double sell_max = row.sell_max;

        MYSQL_BIND bind[8];
        std::memset(bind, 0, sizeof(bind));

        bind[0].buffer_type = MYSQL_TYPE_LONGLONG;
        bind[0].buffer = &unix_ts;

        bind[1].buffer_type = MYSQL_TYPE_STRING;
        bind[1].buffer = recorded_at.data();
        bind[1].buffer_length = static_cast<unsigned long>(recorded_at.size());

        bind[2].buffer_type = MYSQL_TYPE_DOUBLE;
        bind[2].buffer = &best_buy;
        bind[2].is_null = &buy_is_null;

        bind[3].buffer_type = MYSQL_TYPE_DOUBLE;
        bind[3].buffer = &best_sell;
        bind[3].is_null = &sell_is_null;

        bind[4].buffer_type = MYSQL_TYPE_DOUBLE;
        bind[4].buffer = &buy_min;

        bind[5].buffer_type = MYSQL_TYPE_DOUBLE;
        bind[5].buffer = &buy_max;

        bind[6].buffer_type = MYSQL_TYPE_DOUBLE;
        bind[6].buffer = &sell_min;

        bind[7].buffer_type = MYSQL_TYPE_DOUBLE;
        bind[7].buffer = &sell_max;

        if (mysql_stmt_bind_param(stmt_, bind)) {
            std::cerr << "mysql_stmt_bind_param failed: " << mysql_stmt_error(stmt_) << '\n';
            return false;
        }
        if (mysql_stmt_execute(stmt_)) {
            std::cerr << "mysql_stmt_execute failed: " << mysql_stmt_error(stmt_) << '\n';
            return false;
        }

        return true;
    }

private:
    bool ensure_table() {
        static const char* kCreateSql = R"(
            CREATE TABLE IF NOT EXISTS p2p_rates (
                unix_ts BIGINT NOT NULL PRIMARY KEY,
                recorded_at DATETIME NOT NULL,
                best_buy_rate DOUBLE NULL,
                best_sell_rate DOUBLE NULL,
                buy_min DOUBLE NOT NULL DEFAULT 0,
                buy_max DOUBLE NOT NULL DEFAULT 0,
                sell_min DOUBLE NOT NULL DEFAULT 0,
                sell_max DOUBLE NOT NULL DEFAULT 0
            )
        )";

        if (mysql_query(conn_, kCreateSql)) {
            std::cerr << "mysql_query failed: " << mysql_error(conn_) << '\n';
            return false;
        }

        return true;
    }

    MYSQL* conn_;
    MYSQL_STMT* stmt_;
    bool ready_;
};
