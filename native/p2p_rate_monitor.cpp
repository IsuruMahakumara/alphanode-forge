#include "p2p_types.hpp"
#include <httplib.h>
#include <simdjson.h>
#include <fstream>
#include <iostream>

using namespace simdjson;

struct Offer {
    double price = 0;
    double min_amount = 0;
    double max_amount = 0;
};

Offer fetch_best_offer(const std::string& trade_type) {
    httplib::Client cli("https://p2p.binance.com");
    cli.set_connection_timeout(5);
    cli.set_read_timeout(10);
    
    std::string body = R"({"asset":"USDT","fiat":"LKR","tradeType":")" + trade_type + 
                      R"(","page":1,"rows":1,"payTypes":[],"merchantCheck":false})";
    
    auto res = cli.Post("/bapi/c2c/v2/friendly/c2c/adv/search", body, "application/json");
    
    Offer offer;
    if (!res || res->status != 200) return offer;
    
    dom::parser parser;
    dom::element doc;
    auto error = parser.parse(res->body).get(doc);
    if (error) return offer;
    
    std::string_view code;
    error = doc["code"].get_string().get(code);
    if (error || code != "000000") return offer;
    
    dom::array data;
    error = doc["data"].get_array().get(data);
    if (error || data.size() == 0) return offer;
    
    dom::object adv;
    error = data.at(0)["adv"].get_object().get(adv);
    if (error) return offer;
    
    adv["price"].get_double().get(offer.price);
    adv["minSingleTransAmount"].get_double().get(offer.min_amount);
    adv["maxSingleTransAmount"].get_double().get(offer.max_amount);
    
    return offer;
}

int main() {
    P2PRateRecord record;
    record.timestamp = current_timestamp();
    record.unix_timestamp = current_unix_timestamp();
    
    Offer buy = fetch_best_offer("BUY");
    if (buy.price > 0) {
        record.best_buy_rate = buy.price;
        record.buy_min = buy.min_amount;
        record.buy_max = buy.max_amount;
    }
    
    Offer sell = fetch_best_offer("SELL");
    if (sell.price > 0) {
        record.best_sell_rate = sell.price;
        record.sell_min = sell.min_amount;
        record.sell_max = sell.max_amount;
    }
    
    std::ofstream file("rates.jsonl", std::ios::app);
    if (file.is_open()) {
        file << record.to_jsonl() << std::endl;
        std::cout << "Logged: buy=" << record.best_buy_rate.value_or(0) 
                  << " sell=" << record.best_sell_rate.value_or(0) << std::endl;
    }
    
    return 0;
}