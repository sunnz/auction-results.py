#!/usr/bin/env python3

import yaml
import auction.suburb


def main():
    # load config.
    try:
        with open('config.yaml', 'r') as config_file:
            config = yaml.load(config_file)
    except (OSError, IOError):
        print('failed reading config.yaml. :-(')
        exit(1)

    # initialise global settings.
    auction.suburb.Suburb.baseurl = config['baseurl']
    auction.suburb.Suburb.textimageurl = config['textimageurl']

    # load each (geographical) state.
    for config_path, suburbs in config['paths'].items():
        # load html for this (geographical) state.
        try:
            with open('sample.html', 'r') as sample_file:
                auction_data_raw = sample_file.read()
                print('loaded sample.html into auction_data_raw.')
        except (OSError, IOError):
            print('failed reading sample.html data file. :(')
            exit(2)

        # load each suburb.
        for name, suburb_config in suburbs.items():
            sub_emails = suburb_config['emails']
            print('suburb: ' + name)
            print('emails: ' + repr(sub_emails))
            mySuburb = auction.suburb.Suburb(name, config['from'], sub_emails, auction_data_raw)
            #mySuburb._pprint()
            #mySuburb._print_class()
            #print(mySuburb.get_rendered_body('\n'))
            msg = mySuburb.render_msg('\n')
            for email in sub_emails:
                if 'To' in msg:
                    del msg['To']
                msg['To'] = email
                print()
                print(msg.as_string())

if __name__ == '__main__':
    main()