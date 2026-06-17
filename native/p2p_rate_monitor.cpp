#include "common/connect_db.hpp"
#include "common/time.hpp"
#include "p2p/ingest.hpp"

#include <fstream>
#include <iostream>

int main() {
    P2PRateRecord record;
    record.timestamp = current_timestamp();
    record.unix_timestamp = current_unix_timestamp();

    P2PIngest ingest;
    P2POffer buy = ingest.fetch_best_offer("BUY");
    if (buy.valid()) {
        record.best_buy_rate = buy.price;
        record.buy_min = buy.min_amount;
        record.buy_max = buy.max_amount;
    }

    P2POffer sell = ingest.fetch_best_offer("SELL");
    if (sell.valid()) {
        record.best_sell_rate = sell.price;
        record.sell_min = sell.min_amount;
        record.sell_max = sell.max_amount;
    }

    DbConnection db;
    if (!db.connect("binance")) {
        return 1;
    }

    P2PRateInserter inserter(db.handle());
    if (!inserter.ready() || !inserter.insert(record)) {
        return 1;
    }

    std::ofstream file("datalake/p2p_rates.jsonl", std::ios::app);
    if (file.is_open()) {
        file << record.to_jsonl() << '\n';
    }

    std::cout << "buy=" << record.best_buy_rate.value_or(0)
              << " sell=" << record.best_sell_rate.value_or(0) << '\n';
    return 0;
}
