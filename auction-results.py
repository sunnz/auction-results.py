#!/usr/bin/env python3

import sys
import urllib.request
import urllib.error
import bs4
import smtplib
import email.mime.multipart
import email.mime.text
import email.mime.image
import base64
import re
import datetime
import yaml


def main():
    try:
        with open('config.yaml', 'r') as config_file:
            config = yaml.load(config_file)
    except (OSError, IOError):
        print('cannot openfile config.yaml. :-(')
        sys.exit(1)

    baseurl = config['baseurl']
    textimageurl = config['textimageurl']
    from_addr = config['from']

    print('baseurl: ' + baseurl)
    print('textimageurl: ' + textimageurl)
    print('from_addr: ' + from_addr)

    for config_path, suburbs in config['paths'].items():
        path = config_path
        print('path: ' + path)

        auction_data_raw = None
        test = True
        try:
            with open('sample.html', 'r') as sample_file:
                auction_data_raw = sample_file.read()
                print('read sample.html into auction_data_raw.')
                print('test mode on')
        except IOError:
            url = baseurl + path
            response = urllib.request.urlopen(url)
            auction_data_raw = response.read().decode()
            print('download data into auction_data_raw.')
            test = False
            print('test mode off')

        if auction_data_raw:
            with open('data.html', 'w') as f:
                f.write(auction_data_raw)
                print('backed up auction_data_raw to data.html')

            for name, suburb_config in suburbs.items():
                suburb = name
                emails = suburb_config['emails']
                print('suburb: ' + suburb)
                print('emails: ' + repr(emails))
                auction_result(auction_data_raw, baseurl,
                               textimageurl, suburb, test, emails, from_addr)
        else:
            print('no auction data for {path} wo!'.format(path=path))


def auction_result(auction_data_raw, baseurl, textimageurl,
                   suburb, test, emails, from_addr):
    parserlib = 'lxml'
    # parserlib = 'html5lib'

    soup = bs4.BeautifulSoup(auction_data_raw, parserlib)
    selector = '#' + suburb + ' thead {leaf}'
    headers = [
        'Address',
        soup.select(selector.format(
            leaf='div.col-property-price')).pop().string,
        soup.select(selector.format(
            leaf='div.col-num-beds')).pop().string,
        soup.select(selector.format(
            leaf='div.col-property-type')).pop().string,
        soup.select(selector.format(
            leaf='div.col-auction-result')).pop().string,
        soup.select(selector.format(
            leaf='div.col-auction-date')).pop().string,
        soup.select(selector.format(
            leaf='div.col-agent')).pop().string,
    ]

    results = '<!doctype html><html><head></head><body>\n'
    row_template = (
        "<tr style='border:1px solid grey;"
        "font-family:Museo-Sans-300,sans-serif;font-size:10pt'>\n"
        "<th style='font-size:10pt'>\n{header}\n</th>\n"
        "<td style='font-size:10pt;width:50%'>\n{data}\n</td>\n</tr>\n"
    )
    images = []
    for n, row in enumerate(soup.select('#' + suburb + ' tbody tr')):
        row_soup = bs4.BeautifulSoup(str(row), parserlib)
        results += '<table style="border:1px solid grey;width:100%;'
        results += 'margin-bottom:1em">\n'

        addr_tag = row_soup.select('.col-address').pop()
        if 'href' in addr_tag.attrs:
            addr_tag['href'] = baseurl + addr_tag['href']
        results += row_template.format(
            header=headers[0],
            data=str(addr_tag))

        img_fmt = (
            '<img src="cid:{0:d}_price" '
            'style="max-height:17px;height:17px;width:auto">'
        )
        img = img_fmt.format(n)
        results += row_template.format(header=headers[1], data=img)
        img_src = row_soup.select('.col-property-price img').pop()['src']
        image = img_src.replace('data:image/png;base64,', '')
        images.append(('{0:d}_price'.format(n), image))

        img_src = row_soup.select('.col-num-beds img').pop()['src']
        encoded = img_src.replace(textimageurl, '')
        encoded = re.sub(r'\?.*', '', encoded)
        beds = base64.b64decode(encoded).decode()
        results += row_template.format(header=headers[2], data=beds)

        results += row_template.format(
            header=headers[3],
            data=row_soup.select('.col-property-type').pop().string)

        results += row_template.format(
            header=headers[4],
            data=row_soup.select('.col-auction-result').pop().string)

        img_src = row_soup.select('.col-auction-date img').pop()['src']
        encoded = img_src.replace(textimageurl, '')
        encoded = re.sub(r'\?.*', '', encoded)
        date = base64.b64decode(encoded).decode()
        results += row_template.format(header=headers[5], data=date)

        agency_list = row_soup.select('.col-agent a.agency-profile-url')
        if len(agency_list):
            agency = agency_list.pop().string
        else:
            agency = row_soup.select('.col-agent').pop().string
        results += row_template.format(
            header=headers[6],
            data=agency)

        results += '</table>'
    results += '</body></html>'

    msg = email.mime.multipart.MIMEMultipart('alternative')
    msg['Subject'] = 'Auction result for {suburb}: {date}'.format(
        suburb=suburb, date=datetime.date.today().strftime('%Y-%m-%d'))
    msg['From'] = from_addr
    msg.attach(email.mime.text.MIMEText(results, 'html'))

    for name, image in images:
        img = email.mime.image.MIMEImage(
            base64.standard_b64decode(image), _subtype='png')
        img.add_header('Content-ID', '<{name}>'.format(name=name))
        msg.attach(img)

    if test:
        for email_addr in emails:
            del msg['To']
            msg['To'] = email_addr
            print(msg.as_string())
    else:
        s = smtplib.SMTP('localhost')
        for email_addr in emails:
            del msg['To']
            msg['To'] = email_addr
            msg_string = msg.as_string()
            s.sendmail(msg['From'], msg['To'], msg_string)
            print(msg_string)
        s.quit()

if __name__ == '__main__':
    main()
