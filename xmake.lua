add_rules("mode.debug", "mode.release")
set_languages("c++20")

add_requires("simdjson", "cpp-httplib")

target("p2p_monitor")
    set_kind("binary")
    add_files("native/*.cpp")
    add_packages("simdjson", "cpp-httplib")