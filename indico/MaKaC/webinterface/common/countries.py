# -*- coding: utf-8 -*-
##
## $Id: countries.py,v 1.5 2008/06/19 16:07:12 jose Exp $
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

from MaKaC.i18n import _

class CountryHolder:
    
    def __init__(self):
        self._countries = {}
        self._countries['AF'] = "AFGHANISTAN"
        self._countries['AL'] = "ALBANIA"
        self._countries['DZ'] = "ALGERIA"
        self._countries['AS'] = "AMERICAN SAMOA"
        self._countries['AD'] = "ANDORRA"
        self._countries['AO'] = "ANGOLA"
        self._countries['AG'] = "ANTIGUA"
        self._countries['AR'] = "ARGENTINA"
        self._countries['AM'] = "ARMENIA"
        self._countries['AW'] = "ARUBA"
        self._countries['AU'] = "AUSTRALIA"
        self._countries['AT'] = "AUSTRIA"
        self._countries['AZ'] = "AZERBAIJAN"
        self._countries['BS'] = "BAHAMAS"
        self._countries['BH'] = "BAHRAIN"
        self._countries['BD'] = "BANGLADESH"
        self._countries['BB'] = "BARBADOS"
        self._countries['BY'] = "BELARUS"
        self._countries['BE'] = "BELGIUM"
        self._countries['BZ'] = "BELIZE"
        self._countries['BJ'] = "BENIN"
        self._countries['BM'] = "BERMUDA"
        self._countries['BT'] = "BHUTAN"
        self._countries['BO'] = "BOLIVIA"
        self._countries['BA'] = "BOSNIA"
        self._countries['BW'] = "BOTSWANA"
        self._countries['BR'] = "BRAZIL"
        self._countries['VG'] = "BRITISH VIRGIN ISLANDS"
        self._countries['BN'] = "BRUNEI"
        self._countries['BG'] = "BULGARIA"
        self._countries['BF'] = "BURKINA FASO"
        self._countries['BI'] = "BURUNDI"
        self._countries['CA'] = "CANADA"
        self._countries['CV'] = "CAPE VERDE"
        self._countries['KY'] = "CAYMAN Islands"
        self._countries['CF'] = "CENTRAL AFRICAN REPUBLIC"
        self._countries['TD'] = "CHAD"
        self._countries['CL'] = "CHILE"
        self._countries['CN'] = "CHINA"
        self._countries['CC'] = "COCOS Islands"
        self._countries['CO'] = "COLOMBIA"
        self._countries['KM'] = "COMOROS"
        self._countries['CG'] = "CONGO"
        self._countries['CR'] = "COSTA RICA"
        self._countries['HR'] = "CROATIA"
        self._countries['CU'] = "CUBA"
        self._countries['CY'] = "CYPRUS"
        self._countries['CZ'] = "CZECH REPUBLIC"
        self._countries['KP'] = "DEM. PEO. REP. OF KOREA"
        self._countries['KH'] = "DEMOCRATIC KAMPUCHEA"
        self._countries['CD'] = "DEMOCRATIC REPUBLIC OF CONGO"
        self._countries['DK'] = "DENMARK"
        self._countries['DJ'] = "DJIBOUTI"
        self._countries['DM'] = "DOMINICA"
        self._countries['DO'] = "DOMINICAN REPUBLIC"
        self._countries['EC'] = "ECUADOR"
        self._countries['EG'] = "EGYPT"
        self._countries['SV'] = "EL SALVADOR"
        self._countries['GQ'] = "EQUATORIAL GUINEA"
        self._countries['ER'] = "ERITREA"
        self._countries['EE'] = "ESTONIA"
        self._countries['ET'] = "ETHIOPIA"
        self._countries['FJ'] = "FIJI"
        self._countries['FI'] = "FINLAND"
        self._countries['FR'] = "FRANCE"
        self._countries['GF'] = "FRENCH GUIANA"
        self._countries['PF'] = "FRENCH POLYNESIA"
        self._countries['GA'] = "GABON"
        self._countries['GM'] = "GAMBIA"
        self._countries['GE'] = "GEORGIA"
        self._countries['DE'] = "GERMANY"
        self._countries['GH'] = "GHANA"
        self._countries['GI'] = "GIBRALTAR"
        self._countries['GR'] = "GREECE"
        self._countries['GL'] = "GREENLAND"
        self._countries['GD'] = "GRENADA"
        self._countries['GP'] = "GUADELOUPE"
        self._countries['GU'] = "GUAM"
        self._countries['GT'] = "GUATEMALA"
        self._countries['GN'] = "GUINEA"
        self._countries['GW'] = "GUINEA-BISSAU"
        self._countries['GY'] = "GUYANA"
        self._countries['HT'] = "HAITI"
        self._countries['HN'] = "HONDURAS"
        self._countries['HK'] = "HONG-KONG"
        self._countries['HU'] = "HUNGARY"
        self._countries['IS'] = "ICELAND"
        self._countries['IN'] = "INDIA"
        self._countries['ID'] = "INDONESIA"
        self._countries['IR'] = "IRAN"
        self._countries['IQ'] = "IRAQ"
        self._countries['IE'] = "IRELAND"
        self._countries['IL'] = "ISRAEL"
        self._countries['IT'] = "ITALY"
        self._countries['CI'] = "IVORY COAST"
        self._countries['JM'] = "JAMAICA"
        self._countries['JP'] = "JAPAN"
        self._countries['JO'] = "JORDAN"
        self._countries['KZ'] = "KAZAKHSTAN"
        self._countries['KE'] = "KENYA"
        self._countries['KW'] = "KUWAIT"
        self._countries['KG'] = "KYRGYZSTAN"
        self._countries['LA'] = "LAO PEOPLE'S DEM. REP."
        self._countries['LV'] = "LATVIA"
        self._countries['LB'] = "LEBANON"
        self._countries['LS'] = "LESOTHO"
        self._countries['LR'] = "LIBERIA"
        self._countries['LY'] = "LIBYAN ARAB JAMAHIRYA"
        self._countries['LI'] = "LIECHTENSTEIN"
        self._countries['LT'] = "LITHUANIA"
        self._countries['LU'] = "LUXEMBURG"
        self._countries['MO'] = "MACAU"
        self._countries['MK'] = "MACEDONIA, F.Y.R."
        self._countries['MG'] = "MADAGASCAR"
        self._countries['MW'] = "MALAWI"
        self._countries['MY'] = "MALAYSIA"
        self._countries['MV'] = "MALDIVES"
        self._countries['ML'] = "MALI"
        self._countries['MT'] = "MALTA"
        self._countries['MQ'] = "MARTINIQUE"
        self._countries['MR'] = "MAURITANIA"
        self._countries['MU'] = "MAURITIUS"
        self._countries['MX'] = "MEXICO"
        self._countries['MD'] = "MOLDOVA"
        self._countries['MC'] = "MONACO"
        self._countries['MN'] = "MONGOLIA"
        self._countries['ME'] = "MONTENEGRO"
        self._countries['MA'] = "MOROCCO"
        self._countries['MZ'] = "MOZAMBIQUE"
        self._countries['XX'] = "MULTIPLE COUNTRIES"
        self._countries['MM'] = "MYANAMAR"
        self._countries['NA'] = "NAMIBIA"
        self._countries['NP'] = "NEPAL"
        self._countries['AN'] = "NETHERLANDS ANTILLES"
        self._countries['NL'] = "NETHERLANDS"
        self._countries['NC'] = "NEW CALEDONIA"
        self._countries['NZ'] = "NEW ZEALAND"
        self._countries['NI'] = "NICARAGUA"
        self._countries['NE'] = "NIGER"
        self._countries['NG'] = "NIGERIA"
        self._countries['NO'] = "NORWAY"
        self._countries['OM'] = "OMAN"
        self._countries['PK'] = "PAKISTAN"
        self._countries['PA'] = "PANAMA"
        self._countries['PG'] = "PAPUA NEW GUINEA"
        self._countries['PY'] = "PARAGUAY"
        self._countries['PE'] = "PERU"
        self._countries['PH'] = "PHILIPPINES"
        self._countries['PL'] = "POLAND"
        self._countries['PT'] = "PORTUGAL"
        self._countries['PR'] = "PUERTO RICO"
        self._countries['QA'] = "QATAR"
        self._countries['KR'] = "REPUBLIC OF KOREA"
        self._countries['RE'] = "REUNION"
        self._countries['RO'] = "ROMANIA"
        self._countries['RU'] = "RUSSIA"
        self._countries['RW'] = "RWANDA"
        self._countries['LC'] = "SAINT LUCIA"
        self._countries['SM'] = "SAN MARINO"
        self._countries['ST'] = "SAO TOME - PRINCIPE"
        self._countries['SA'] = "SAUDI ARABIA"
        self._countries['SN'] = "SENEGAL"
        self._countries['RS'] = "SERBIA"
        self._countries['SC'] = "SEYCHELLES"
        self._countries['SL'] = "SIERRA LEONE"
        self._countries['SG'] = "SINGAPORE"
        self._countries['SK'] = "SLOVAKIA"
        self._countries['SI'] = "SLOVENIA"
        self._countries['SO'] = "SOMALIA"
        self._countries['ZA'] = "SOUTH AFRICA"
        self._countries['ES'] = "SPAIN"
        self._countries['LK'] = "SRI LANKA"
        self._countries['SD'] = "SUDAN"
        self._countries['SR'] = "SURINAM"
        self._countries['SE'] = "SWEDEN"
        self._countries['CH'] = "SWITZERLAND"
        self._countries['SY'] = "SYRIEN ARAB REPUBLIC"
        self._countries['TW'] = "TAIWAN, PROVINCE OF CHINA"
        self._countries['TJ'] = "TAJIKISTAN"
        self._countries['TH'] = "THAILAND"
        self._countries['TG'] = "TOGO"
        self._countries['TO'] = "TONGA"
        self._countries['TT'] = "TRINIDAD TOBAGO"
        self._countries['TN'] = "TUNISIA"
        self._countries['TR'] = "TURKEY"
        self._countries['TM'] = "TURKMENISTAN"
        self._countries['UG'] = "UGANDA"
        self._countries['UA'] = "UKRAINE"
        self._countries['TZ'] = "UN. REP. OF TANZANIA"
        self._countries['CM'] = "UN.-REP. OF CAMEROON"
        self._countries['AE'] = "UNITED ARAB EMIRATES"
        self._countries['GB'] = "UNITED KINGDOM"
        self._countries['US'] = "UNITED STATES OF AMERICA"
        self._countries['UY'] = "URUGUAY"
        self._countries['SU'] = "USSR"
        self._countries['UZ'] = "UZBEKISTAN"
        self._countries['VA'] = "VATICAN CITY STATE"
        self._countries['VE'] = "VENEZUELA"
        self._countries['VN'] = "VIETNAM"
        self._countries['EH'] = "WESTERN SAHARA"
        self._countries['YD'] = "YEMEN DEMOCRATIC"
        self._countries['YE'] = "YEMEN"
        self._countries['ZM'] = "ZAMBIA"
        self._countries['ZW'] = "ZIMBABWE"    

    def getCountries(self):
        return self._countries

    def getCountryList( self ):
        return self._countries.values()
    
    def getCountryById( self, id ):
        return self._countries.get(id, "")
    
    def getCountryKeys(self):
        return self._countries.keys()

    def getCountrySortedKeys(self):
        keys = self.getCountryKeys()
        keys.sort(self._sortByValue)
        return keys

    def _sortByValue(self, v1, v2):
        return cmp(self._countries[v1], self._countries[v2])
