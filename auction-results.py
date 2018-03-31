#!/usr/bin/env python3

import yaml
import smtplib
import requests
import urllib.error
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
            url = '{base}/{path}'.format(base=config['baseurl'], path=config_path)
            headers = {}
            headers['User-Agent'] = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11;'
                ' rv:47.0) Gecko/20100101 Firefox/47.0')
            headers['DNT'] = '1'
            headers['Accept'] = ('text/html,application/xhtml+xml,application/xml;'
                'q=0.9,*/*;q=0.8')
            headers['Accept-Language'] = 'en-GB,en;q=0.5'
            headers['Accept-Encoding'] = 'gzip, deflate, br'
            req = requests.get(url, headers=headers)
            auction_data_raw = req.text

        # load each suburb.
        for name, suburb_config in suburbs.items():
            sub_emails = suburb_config['emails']
            print('suburb: ' + name)
            print('emails: ' + repr(sub_emails))
            mySuburb = auction.suburb.Suburb(name, config['from'], sub_emails, auction_data_raw)
            msg = mySuburb.render_msg('\n')

            # send out results.
            s = smtplib.SMTP('localhost')
            results = []
            for email in sub_emails:
                if 'To' in msg:
                    del msg['To']
                msg['To'] = email

                if True == config['live']:
                    s.send_message(msg)

                results.append(msg.as_string())
            s.quit()
            print('\n'.join(results))

if __name__ == '__main__':
    main()
