#!/usr/bin/python
# -*- coding: utf-8 -*-

import bs4
import requests
import googledatastore as datastore


def process_page(soup):
  started = False
  request = datastore.CommitRequest()
  request.mode = datastore.CommitRequest.NON_TRANSACTIONAL

  for row in soup.find('table').find_all('table')[-1].findAll('tr'):
    columns = [
        (''.join(y.strip() for y in x.strings)
          .replace(u'\x80', u'€'))
        for x in row.findAll('td')]
    if 'Year' in columns:
      continue
    link = 'http://planecheck.com/' + row.find('a').get('href')
    _, list_id = link.rsplit('=', 1)
    manufacturer, model = columns[0].split(u'\xa0')
    year, raw_price, country, views = columns[1:]
    if not u'\xa0' in raw_price:
      price = None
      currency = None
    else:
      price, currency = raw_price.split(u'\xa0')
      price = int(price.replace('.', ''))

    entity = request.mutation.upsert.add()
    path = entity.key.path_element.add()
    path.kind = 'Manufacturer'
    path.name = manufacturer
    path = entity.key.path_element.add()
    path.kind = 'Model'
    path.name = model
    path = entity.key.path_element.add()
    path.kind = 'Listing'
    path.name = 'planecheck.com ' + list_id

    if price:
      prop = entity.property.add()
      prop.name = 'price'
      prop.value.integer_value = price
      prop = entity.property.add()
      prop.name = 'currency'
      prop.value.string_value = currency
    prop = entity.property.add()
    prop.name = 'views'
    prop.value.integer_value = int(views)
    prop = entity.property.add()
    prop.name = 'link'
    prop.value.string_value = link
    prop = entity.property.add()
    prop.name = 'manufacturer'
    prop.value.string_value = manufacturer
    prop = entity.property.add()
    prop.name = 'model'
    prop.value.string_value = model
    prop = entity.property.add()
    prop.name = 'country'
    prop.value.string_value = country
    prop = entity.property.add()
    prop.name = 'year'
    prop.value.integer_value = int(year)
  datastore.commit(request)


r = requests.get('http://planecheck.com/aspsel2.asp?parmstr=&page=0')
soup = bs4.BeautifulSoup(r.text, 'html.parser')

datastore.set_options(dataset='bluecmd0')

pages = set()
for link in soup.find_all('a'):
  href = link.get('href')
  if href.startswith('aspsel2.asp?'):
    pages.add(href)

process_page(soup)

for page in pages:
  r = requests.get('http://planecheck.com/' + page)
  soup = bs4.BeautifulSoup(r.text, 'html.parser')
  process_page(soup)


