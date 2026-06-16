add_rules("mode.debug", "mode.release")
set_languages("c++20")

add_requires("simdjson", "cpp-httplib")

target("p2p_monitor")
    set_kind("binary")
    add_files("native/p2p_rate_monitor.cpp")
    add_includedirs("native")
    add_packages("simdjson", "cpp-httplib")
    add_syslinks("mysqlclient")
    if is_plat("macosx") then
        add_includedirs("/opt/homebrew/opt/mysql-client/include")
        add_linkdirs("/opt/homebrew/opt/mysql-client/lib")
    end
