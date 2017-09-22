import os
import sys
import re
import subprocess
import numpy
import sqlite3
from pathlib import Path
import shutil

import threading
import time

max_cpu = 4
processing = 0
multi_l3p = False;

###########################################
#### batch multicore command-line processing
def call_batch(command):
    global processing
    processing += 1
    #print("running command: {}".format(command))
    #print(command)
    process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    process.wait()
    processing -= 1
###########################################
###########################################



most_common_first = True

conn = sqlite3.connect('/app/inventory.db')
c = conn.cursor()

background_opt = "-b.9,.9,.9" # gray background
lights_include_opt = "-il/app/lights.pov"
height_opt = '+H480'
width_opt = '+W640'


povfile_re = re.compile('\.pov', re.IGNORECASE)



radius = -50
lats = [-70,-50,-30,30,50,70]
#lats = numpy.arange(-70, 70, 20)
lons = numpy.arange(-180, 170, 45)

# debug stuff
#lats = [45]
#lons = [90]


# get color lookups - we will use the hex values allowed by l3p
color_lookup = {} # key: integer, value: hex color
for row in c.execute("select id, name, rgb, is_trans from colors"):
    prefix = "0x02"
    is_trans = False
    if row[3] == 't':
        # transparent
        prefix = "0x03"
        is_trans = True
    hex_color = row[2]
    color_id = row[0]
    color_lookup[color_id] = {'hex': "{}{}".format(prefix, hex_color), 'name': row[1], 'transparent': is_trans}


os.makedirs('/data/pov', exist_ok=True)


# go through inventory and only generate images that are valid part/color combinations
#c.execute("select part_num, name from parts where part_cat_id not in (13,17,27,57)")
#part_rows = c.fetchall()

q = "select p.name, i.part_num, i.color_id, sum(i.quantity) as count from inventory_parts i join parts p USING(part_num) where p.part_cat_id not in (13,17,27,57) group by part_num, color_id order by count desc"
# name, part color, count

c.execute(q)
part_rows = c.fetchall()

# track how far we've gone
part_num = 0
part_count = len(part_rows)

for p_row in part_rows:
    part_name = p_row[0]
    part = p_row[1]
    color = p_row[2]

    part_num += 1
    pctDone = part_num / part_count
    print("### PART {} OF {} ( {:.3f}% complete )".format(part_num, part_count, pctDone))
    sys.stdout.flush()

    povBase = Path("/data/pov")
    # check if the part is in the ldraw library
    part_name_path = povBase / part
    extended_part_name = part_name.replace("/","-")
    extended_part_name = extended_part_name.replace(" ","_").encode('utf-8','ignore')
    part_file = Path("/opt/ldraw/parts", part).with_suffix('.dat')
    if not part_file.is_file():
        #something is wrong. resolve re-named parts somehow?
        print("OOPS - part {} could not be found!".format(part))
        continue

    part_name_path.mkdir(parents=True,exist_ok=True)

    # get hex value of color:
    color_hex = color_lookup[color]['hex']
    color_name = color_lookup[color]['name']
    trans = color_lookup[color]['transparent']
    color_name.replace(" ", "_")
    colored_path = part_name_path / color_name
    colored_path.mkdir(parents=True,exist_ok=True)
    print("rendering -- part#{}: {} -> color: {} ({})".format(part, extended_part_name, color_name, "Transparent" if trans else "Opaque"))
    sys.stdout.flush()
    fname = "{}.dat".format(part)
    for lat in lats:
        for lon in lons:
            if lon == -180:
                lon = -179  # silly bug? sometimes camera is not pointed at part
            pov_fname = "{}_{}_{}.pov".format(part, lat, lon)
            pov_f_path = colored_path / pov_fname
            color_opt = "-c{}".format(color_hex)
            cg_opt = "-cg{},{},{}".format(lat, lon, radius)
            # does the output file already exist?
            if Path(pov_f_path).exists():
                print("{} exists. skipping.".format(pov_f_path))
                continue
            l3p_cmd = ['l3p', background_opt, '-q4', color_opt, lights_include_opt, cg_opt, '-bu', '-o', fname, str(pov_f_path)]
            if multi_l3p:
                while processing > max_cpu:
                    time.sleep(1)
                t = threading.Thread(target=call_batch, args=(l3p_cmd,))
                t.daemon = True
                t.start()
            else:
                # no-multi
                subprocess.run(l3p_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)





# all done with the l3p generation.
# now start on processing bathces of POV-ray files




Path("/data/img").mkdir(parents=True, exist_ok=True)

for root, dirs, files in os.walk('/data/pov'):
    for f in files:
        file = os.path.join(root, f)
        filename, file_extension = os.path.splitext(f)
        ext = file_extension[1:]
        if ext == 'pov':
            while processing > max_cpu:
                time.sleep(1)
            print("looking at file: {}".format(file))
            pov_fname = file
            rendered_root = root.replace("/pov/", "/img/")
            out_fname = str(Path(rendered_root, filename).with_suffix('.png'))
            out_fname_opt = "+O{}".format(out_fname)
            Path(rendered_root).mkdir(parents=True, exist_ok=True)
            pov_cmd = ['povray', height_opt, width_opt, '+A', '+Q9', '-GA', pov_fname, out_fname_opt]
            if Path(out_fname).exists():
                print("{} exists. skipping.".format(out_fname))
            else:
                t = threading.Thread(target=call_batch, args=(pov_cmd,))
                t.daemon = True
                t.start()




# l3p -bWhite -q4 -c4 -cg10,45,-50 -o 27c.dat pov/ && cd pov && povray +H480 +W640 +A +Q9 *.pov

        # l3p -bWhite -q4 -c4 -cg50,45,-50 -o 11598.dat && povray +H480 +W640 +A +Q9 -GA 11598.pov