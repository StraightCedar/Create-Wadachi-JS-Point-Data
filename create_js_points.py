#!/usr/bin/python
# coding: UTF-8

import sys
from sys import argv
import os
import datetime
from decimal import Decimal, ROUND_HALF_UP, ROUND_HALF_EVEN

# Show usage.
def ShowUsage():
    print("Usage: python " + os.path.basename(__file__) + " input-nmea-file-name <output-js-file-name>")

# Get input & output file names.
def GetInputFileName():
    # Get input file name.
    if len(sys.argv) < 2:
        ShowUsage()
        sys.exit(1)
    input_file = sys.argv[1]
    output_file = ''
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        name_body, _ = os.path.splitext(input_file)
        output_file = '.'.join([name_body+'js-points', 'js'])
    print('in = %s, out = %s' % (input_file, output_file) )
    return(input_file, output_file)

# Index of NMEA Array
IDX_COMMON_UTC_TIME  = 1    # hhmmss.ss in UTC
IDX_GPGGA_LATITUDE   = 2    # 緯度 dddmm.mmmm
IDX_GPGGA_LONGITUDE  = 4    # 経度 dddmm.mmmm
IDX_GPGGA_ANTENA_ALT = 9    # 高度 [m]
IDX_GPRMC_UTC_DATE   = 9    # ddmmyy in UTC

# Get splited NMEA factors as an array.
# Check sum is removed.
def GetNMEAArray(nmea_str):
    nmea_arr = nmea_str.split(',')
    nmea_arr[-1] = nmea_arr[-1].split('*')[0]
    return(nmea_arr)

# Convert latitude or longitude from dddmm.mmmm to ddd.dddd
def ConvDmmToDdd(dmm_val):
    val_q, val_mod = divmod(dmm_val, 100)
    ddd_val = val_q + val_mod / 60
    return(ddd_val)

weekday_arr = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
month_arr   = [None, 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

# NMEA クラス
class Nmea:
    __dmm_lat  = None
    __ddd_lat  = None
    __dmm_lon  = None
    __ddd_lon  = None
    __altitude = None
    __datetime = None

    def __init__(self, gpgga_str, gprmc_str):
        gpgga_arr = GetNMEAArray(gpgga_str)
        gprmc_arr = GetNMEAArray(gprmc_str)
        self.__dmm_lat  = float(gpgga_arr[IDX_GPGGA_LATITUDE])
        self.__dmm_lon  = float(gpgga_arr[IDX_GPGGA_LONGITUDE])
        self.__ddd_lat  = ConvDmmToDdd(self.__dmm_lat)
        self.__ddd_lon  = ConvDmmToDdd(self.__dmm_lon)
        self.__altitude = float(gpgga_arr[IDX_GPGGA_ANTENA_ALT])
        print('self.__ddd_lat = %f, self.__ddd_lon, = %f, self.__altitude = %f' % (self.__ddd_lat, self.__ddd_lon, self.__altitude))
        # 日時の変換
        #track[0].push(new TrackPoint(36.360637, 138.848540, 35.731, 285, 0, 0, "Sun Feb 3 2019 15:55:14"));
        hhmmss, millisec = gprmc_arr[IDX_COMMON_UTC_TIME].split('.')
        ddmmyy     = gprmc_arr[IDX_GPRMC_UTC_DATE]
        utc_dt_obj = datetime.datetime(2000 + int(ddmmyy[4:6]), int(ddmmyy[2:4]), int(ddmmyy[0:2]),\
            int(hhmmss[0:2]), int(hhmmss[2:4]), int(hhmmss[4:6]), int(millisec) * 1000)
        jst_dt_obj = utc_dt_obj + datetime.timedelta(hours = 9)
        date_str = ' '.join([str(n) for n in \
            [weekday_arr[jst_dt_obj.weekday()], month_arr[jst_dt_obj.month], jst_dt_obj.day, jst_dt_obj.year]])
        time_str = ':'.join([str(n) for n in [jst_dt_obj.hour, jst_dt_obj.minute, jst_dt_obj.second]])
        self.__datetime = ' '.join([date_str, time_str])
        print('self.__datetime = %s' % [self.__datetime])

    # オブジェクトが有効か否か
    def IsAvalable(self):
        return(self.__dmm_lat is not None)
    
    def GetDddLatitude(self):
        return(self.__ddd_lat)

    def GetDddLongitude(self):
        return(self.__ddd_lon)

    def GetAltitude(self):
        return(self.__altitude)

    def GetDatetimeStr(self):
        return(self.__datetime)



# GPGGA 文字列か？
def IsGpgga(nmea_str):
    return('$GPGGA' == nmea_str[0:6])

# コメント文字列か？
def IsComment(line):
    return('@' == line[0])

# 轍の Js 用ポイントでデータを出力する
# GPGGA の次に GPRMC が続くことを前提とする。
def OutputJSPoints(input_file, output_file):
    # Scan input file.
    of = open(output_file, "w")
    with open(input_file, "r") as f:
        gpgga_str = None
        for line in f:
            nmea_str = line.strip()
            if IsComment(nmea_str):
                continue
            if IsGpgga(nmea_str):
                gpgga_str = nmea_str
            else:
                nmea_obj = Nmea(gpgga_str, nmea_str)
                rounded_altitude = Decimal(str(nmea_obj.GetAltitude())).quantize(Decimal('0'), rounding=ROUND_HALF_UP)
                #track[0].push(new TrackPoint(36.360637, 138.848540, 35.731, 285, 0, 0, "Sun Feb 3 2019 15:55:14"));
                push_str = '\ttrack[0].push(new TrackPoint(%f, %f, 0.0, %d, 0, 0, "%s"));' %\
                    (nmea_obj.GetDddLatitude(), nmea_obj.GetDddLongitude(), rounded_altitude, nmea_obj.GetDatetimeStr())
                print('push_str = %s' % push_str)
                of.write(push_str + '\n')
    of.close()
            
# Main
if __name__ == "__main__":
    input_file, output_file = GetInputFileName()
    OutputJSPoints(input_file, output_file)


                

