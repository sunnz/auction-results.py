#!/usr/bin/env python3

import yaml
import smtplib
import requests
import urllib.error
import auction.suburb


def test_auctionresults():
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
        with open('sample.html', 'r') as sample_file:
            auction_data_raw = sample_file.read()
        assert auction_data_raw is not None

        # load each suburb.
        for name, suburb_config in suburbs.items():
            sub_emails = suburb_config['emails']
            print('suburb: ' + name)
            print('emails: ' + repr(sub_emails))
            mySuburb = auction.suburb.Suburb(
                name, config['from'], sub_emails, auction_data_raw
            )
            msg = mySuburb.render_msg('\n')

            # send out results.
            s = smtplib.SMTP('localhost')
            results = []
            for email in sub_emails:
                if 'To' in msg:
                    del msg['To']
                msg['To'] = email

                results.append(msg.as_string())
            s.quit()
            print('\n'.join(results))


if __name__ == '__main__':
    test_auctionresults()
