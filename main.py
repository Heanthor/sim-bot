from api.wowprogress import WarcraftLogs


def main():
    w = WarcraftLogs("dff497843493eac64fdcdd2eba4a9a1f")
    print w.get_all_parses("Heanthor", "fizzcrank", "US", "dps")

if __name__ == '__main__':
    main()
