#pragma once
#include <string>
#include <optional>
#include <chrono>

struct P2PRateRecord {
    std::string timestamp;
    int64_t unix_timestamp;
    std::optional<double> best_buy_rate;
    std::optional<double> best_sell_rate;
    double buy_min = 0;
    double buy_max = 0;
    double sell_min = 0;
    double sell_max = 0;
    
    std::string to_jsonl() const {
        std::string json = "{\"timestamp\":\"" + timestamp + 
                          "\",\"unix_timestamp\":" + std::to_string(unix_timestamp);
        
        if (best_buy_rate) json += ",\"best_buy_rate\":" + std::to_string(*best_buy_rate);
        if (best_sell_rate) json += ",\"best_sell_rate\":" + std::to_string(*best_sell_rate);
        
        json += ",\"buy_min\":" + std::to_string(buy_min) +
                ",\"buy_max\":" + std::to_string(buy_max) +
                ",\"sell_min\":" + std::to_string(sell_min) +
                ",\"sell_max\":" + std::to_string(sell_max) + "}";
        return json;
    }
};

inline std::string current_timestamp() {
    auto now = std::chrono::system_clock::now();
    auto now_c = std::chrono::system_clock::to_time_t(now);
    std::string ts = std::ctime(&now_c);
    ts.pop_back(); // remove newline
    return ts;
}

inline int64_t current_unix_timestamp() {
    return std::chrono::duration_cast<std::chrono::seconds>(
        std::chrono::system_clock::now().time_since_epoch()
    ).count();
}