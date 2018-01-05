# Free for personal use. Prohibited from commercial use without consent.
import re
def get_vis(metar):
  match = re.search('( [0-9] )?([0-9]/?[0-9]?SM)', metar)
  if(match == None):
    return 'INVAILD'
  (g1, g2) = match.groups()
  if(g2 == None):
    return 'INVALID'
  if(g1 != None):
    return 'IFR'
  if '/' in g2:
    return 'LIFR'
  vis = int(re.sub('SM','',g2))
  if vis < 3:
    return 'IFR'
  if vis <=5 :
    return 'MVFR'
  return 'VFR'

print get_vis('KRNT 132053Z 33010KT 10SM SCT034 SCT041 23/14 A3001 RMK AO2 SLP165')
print get_vis('KRNT 132053Z 33010KT 4SM SCT034 SCT041 23/14 A3001 RMK AO2 SLP165')
print get_vis('KRNT 132053Z 33010KT 3SM SCT034 SCT041 23/14 A3001 RMK AO2 SLP165') 
print get_vis('KRNT 132053Z 33010KT 2 1/2SM SCT034 SCT041 23/14 A3001 RMK AO2 SLP165') 
print get_vis('KRNT 132053Z 33010KT 2SM SCT034 SCT041 23/14 A3001 RMK AO2 SLP165') 
print get_vis('KRNT 132053Z 33010KT 1SM SCT034 SCT041 23/14 A3001 RMK AO2 SLP165') 
print get_vis('KRNT 132053Z 33010KT 1/2SM SCT034 SCT041 23/14 A3001 RMK AO2 SLP165') 
