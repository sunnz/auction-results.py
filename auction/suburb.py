#!/usr/bin/env python3

import bs4
import hashlib
import re
import base64
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from pprint import pprint


class Suburb:
    parserlib = 'lxml'
    # parserlib = 'html5lib'
    baseurl = textimageurl = None

    def __init__(self, name=None, sender_email=None, sub_emails=None, data=None):
        self.soup = None
        self.body = []
        self.properties = None
        self.name = name
        self.sender_email =  sender_email
        self.heading = None
        self.attachments = []

        if not sub_emails:
            self.sub_emails = []
        else:
            self.sub_emails = sub_emails

        self.data = data
        if self.data:
            self.process()

    def process(self):
        soup = bs4.BeautifulSoup(self.data, self.parserlib)
        body = ['<!doctype html><html><head></head><body>']
        properties = {}
        attachments = []

        # search for suburb.
        thead_rows = soup.select('#' + self.name + ' thead tr')
        if len(thead_rows) >= 1:
            # save heading.
            self.heading = thead_rows[0]
        else:
            # no result for this suburb.
            body.append("<p>There were no results for {suburb_name}.</p>".format(
                suburb_name=self.name))

        # go through each property in the suburb.
        for row in soup.select('#' + self.name + ' tbody tr'):
            #property_soup = bs4.BeautifulSoup(str(row), self.parserlib)
            body.append('<table style="border:1px solid grey;width:100%;'
                        'margin-bottom:1em">')

            # id.
            id = self._get_property_id(row)
            properties[id] = {}

            # cells of this property.
            cells = [tag for cell in row.select('td') for tag in cell.children if isinstance(tag, bs4.element.Tag)]
            for cell in cells:
                cell_name = cell['class'][0]
                properties[id][cell_name] = self._process_property_feature(cell_name, cell)
                if 'markup' in properties[id][cell_name]:
                    body.append(properties[id][cell_name]['markup'])
                if 'attachment' in properties[id][cell_name]:
                    attachments.append(properties[id][cell_name]['attachment'])
            body.append('</table>')
        body.append('</body></html>')

        self.soup = soup
        self.properties = properties
        self.body = body
        self.attachments = attachments

    def render_msg(self, separator=None):
        msg = MIMEMultipart('alternative')
        msg['From'] = self.sender_email
        msg['Subject'] = 'Auction result for {suburb}: {date}'.format(
            suburb=self.name, date=datetime.date.today().strftime('%Y-%m-%d'))

        # message body.
        if None == separator:
            separator = ''
        msg.attach(MIMEText(self.get_rendered_body(separator), 'html'))
        #msg.attach(MIMEText(self.get_rendered_body(separator), 'html', 'utf-8'))

        # add attachments.
        images = self.get_images()
        attached = []
        for image in images:
            # if not already attached to msg.
            if image['id'] not in attached:
                mime_image = MIMEImage(
                    base64.standard_b64decode(image['data']), _subtype=image['_subtype'])
                mime_image.add_header('Content-ID', '<{id}>'.format(id=image['id']))
                msg.attach(mime_image)
                attached.append(image['id'])

        return msg

    def get_rendered_body(self, separator=None):
        rendered_body = ''

        if None == separator:
            separator = ''

        if None != self.body:
            rendered_body = separator.join(self.body)

        return rendered_body

    def get_images(self):
        images = []

        if None != self.attachments:
            images = [attachment for attachment in self.attachments if 'image' == attachment['type']]

        return images

    def _get_property_id(self, bs_tag):
        address = bs_tag.select('.col-address').pop()
        return hashlib.sha1(address.string.encode()).hexdigest()

    def _process_property_feature(self, type, bs_tag):
        feature = {'bs_tag': bs_tag}
        feature = {}
        heading = data = attachment = None

        html_template = (
            "<tr style='border:1px solid grey;"
            "font-family:Museo-Sans-300,sans-serif;font-size:10pt'>"
            "<th style='font-size:10pt'>{heading}</th>"
            "<td style='font-size:10pt;width:50%'>{data}</td></tr>"
        )

        if 'col-address' == type:
            heading = 'Address'
            data = self._process_property_addr(bs_tag)
        else:
            heading = self._get_heading(type)
            if 'col-property-price' == type:
                data, attachment = self._process_property_price(bs_tag)
            elif 'col-num-beds' == type or 'col-auction-date' == type:
                data = self._process_property_text_base64(bs_tag)
            elif len(bs_tag.contents) >= 1:
                data = bs_tag.contents[0].string

        if None != data:
            feature['markup'] = html_template.format(heading=heading, data=data)

        if None != attachment:
            feature['attachment'] = attachment

        return feature

    def _process_property_addr(self, bs_tag):
        if 'href' in bs_tag.attrs:
            bs_tag['href'] = self.baseurl + bs_tag['href']
        return bs_tag

    def _process_property_price(self, bs_tag):
        data = attachment = None

        # get base64 image.
        img_tag = bs_tag.select('img').pop()
        base64_image = img_tag['src'].replace('data:image/png;base64,', '')
        hash = hashlib.sha1(base64_image.encode()).hexdigest()
        attachment = {
            'id': hash,
            'type': 'image',
            'data': base64_image,
            '_subtype': 'png',
        }

        # build html.
        img_template = (
            '<img src="cid:{hash}" '
            'style="max-height:17px;height:17px;width:auto">'
        )
        data = img_template.format(hash=hash)

        return data, attachment

    def _process_property_text_base64(self, bs_tag):
        img_tag = bs_tag.select('img').pop()
        # remove the front, domain and some paths.
        src = img_tag['src'].replace(self.textimageurl + '/', '')
        # remove the end after the ?
        b64string = re.sub(r'\?.*', '', src)
        return base64.b64decode(b64string).decode()

    def _get_heading(self, type):
        bs_tag = self.heading.select(".{type}".format(type=type)).pop()
        return bs_tag.string

    def _append_body(self, body_string):
        if None == self.body:
            self.body = []
        self.body.append(body_string)

    def _pprint(self):
        dict = self.__dict__.copy()
        dict['data'] = dict['data'][:60]
        if None != self.soup:
            dict['soup'] = self.soup.title.string
        pprint(dict)

    def _print_class(self):
        print('baseurl: {}'.format(self.baseurl))
        print('textimageurl: {}'.format(self.textimageurl))
