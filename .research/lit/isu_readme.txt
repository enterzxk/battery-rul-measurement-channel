 
1 
Description of ISU-ILCC Battery Aging Dataset 
1. General Information 
1.1. Data title: ISU-ILCC Battery Aging Dataset 
1.2. Authors 
▪ Tingkai Li  
Iowa State University (Present Affiliation: University of Connecticut) 
ORCID: 0000-0003-1934-1000 
Emails: tkl@iastate.edu; tingkai.li@uconn.edu  
▪ Jinqiang Liu 
Iowa State University 
ORCID: 0000-0002-1106-6473 
Email: jinqiang@iastate.edu  
▪ Adam Thelen 
Iowa State University 
ORCID: 0000-0001-5443-3678 
Email: acthelen@iastate.edu  
▪ Chad Tischer 
Iowa Lakes Community College 
Email: ctischer@iowalakes.edu  
▪ Chao Hu (Corresponding author) 
Iowa State University (Present Affiliation: University of Connecticut) 
ORCID: 0000-0001-9228-7675 
Emails: chaohu@iastate.edu; chao.hu@uconn.edu 
1.3. Associated publication:  
Predicting Battery Lifetime Under Varying Usage Conditions from Early Aging Data 
(The preprint is available on arXiv at: https://doi.org/10.48550/arXiv.2307.08382)  
 
 
 
2 
2. Dataset Overview 
The ISU-ILCC battery aging dataset was collected jointly by the System Reliability and Safety 
Laboratory at Iowa State University (ISU), now the Reliability Engineering and Informatics 
Laboratory (REIL) at the University of Connecticut, and Iowa Lakes Community College (ILCC). 
The dataset is designed to study the dependency of battery capacity fade from three stress factors: 
charge rate, discharge rate, and depth of discharge. The dataset contains cycle aging data from 251 
lithium-ion (Li-ion) polymer cells (also called lithium polymer cells) cycled under 63 unique 
conditions.  
 
3. Experiment Design 
3.1. Cell specification 
The battery cells used in this aging test campaign are 502030 Li-ion polymer cells manufactured 
by Shenzhen Honghaosheng Electronics Co., Ltd. in Shenzhen, China. These cells have lithium 
nickel manganese cobalt oxide (NMC) as the cathode active material and graphite as the anode 
active material. The rated capacity is 250 mAh, and the operating voltage window is between 3.0 
V and 4.2 V. 
3.2. Test equipment 
The cells were cycle-aged using two 64-channel Neware BTS-4000 battery cyclers, one located at 
ISU and the other one at ILCC. Cells’ terminals were clipped to individual cell holders and placed 
inside two Thermo Scientific™ incubators set at a constant temperature of 30 °C. Figure 2 shows 
the equipment setup at ILCC, which is also similar to the one at ISU.  
 
Figure 1: Summary of test conditions and sequence. 
 
3 
 
Figure 2: Equipment setup at ILCC. 
 
3.3. Regular cycling test 
The regular cycling test was designed with three varying stress factors: charging C-rate, 
discharging C-rate, and depths of discharge (DoD). One charge/discharge cycle consisted of a 
constant-current/constant-voltage (CC/CV) charging step and a constant-voltage discharging step. 
The depths of discharge for different groups were determined by estimating the voltage cutoffs 
during the CC discharging step. The cycling profiles are shown in Figure 3. 
 
Figure 3: Charge and discharge profiles for the cycling test. 
3.4.Reference performance test 
64-channel Neware BTS 
4000 cycler
Thermo Scientific™
HERATHERM incubator
Rack for individual cell 
holders
 
4 
A reference performance test (RPT) was periodically run on every cell to measure the full discharge 
capacity and collect data for lifetime prediction. Using an RPT to check cell capacity is important 
for measuring the full capacity of cells cycled with partial DoDs. During the RPT, two full cycles 
of CC/CV charging and CC discharging at different cycling rates were performed, one at C/5 and 
the other at C/2. The RPT discharge capacity at C/5 is used in generating capacity fade plots. The 
voltage-capacity data from a complete C/5 discharge cycle are used for feature extraction lifetime 
prediction. Additionally, for groups 30–64, we added a cycle with pulse tests at different SoC levels 
to obtain the DC internal resistances. The RPT profiles are shown in Figure 4.  
The RPT is performed after 7 days of cycling. Groups 20 through 64 have an additional RPT after 
the first 3.5 days of cycling (i.e., after the first half week of cycling) to better capture the initial 
capacity fade. 
3.5. Cell ID 
Each cell was assigned a unique identifier (i.e., cell ID) that consisted of the cell’s group number 
and the cell’s index within the group. For example. G3C1 is the first cell in group three. 
4. Data Structure 
In the published dataset, each cell has two separate data files, one for the RPT data and the other 
for the cycling data. All data files are processed using Python and saved in JSON format. Files are 
named by the cell ID. To convert the data to Python dictionaries, a sample code has been provided 
with this dataset (“load_data.py”).  
 
Figure 4: Charge and discharge profiles for the RPT. 
 
 
5 
* The 0.5-week RPT is only for groups 20–64. 
Notation 
Description 
Unit 
Capacity_discharge 
Capacity_charge 
Total Capacity discharged or charged of a 
specific cycle. 
Ah 
start_stop_time (RPT) Start and stop time of a specific RPT.  
(For calculating time on test) 
YYYY-MM-DD 
hh:mm:ss 
start_stop_time 
(Cycling) 
Start and stop time of a specific week’s cycling. 
(For calculating time on test) 
YYYY-MM-DD 
hh:mm:ss 
time_series_charge 
time_series_discharge 
The start and stop times of each cycle’s 
charging and discharging steps. 
YYYY-MM-DD 
hh:mm:ss 
Q 
Charge recordings during a specific cycle. 
Ah 
V 
Voltage recordings during a specific cycle. 
V 
I 
Current recordings during a specific cycle. 
A 
E 
Energy recordings during a specific cycle. 
Wh 
t 
Time stamps of recordings during a specific 
cycle 
YYYY-MM-DD 
hh:mm:ss 
 
4.1. File directory 
1. RPT_json [folder] – Raw data 
1.1. G1C1.json … G64C4.json – RPT data for each cell in JSON format. 
2. Cycling_json [folder] – Raw data 
2.1. G1C1.json … G64C4.json – Cycling data for each cell in JSON format. 
3. Q_interpolated [folder] – Processed data 
3.1. G1C1.csv … G64C4.csv – Interpolated Q data with respect to a voltage vector 
containing 1000 elements equally spaced between 3V and 4.2V. Each column contains 
the Q reading from one RPT. 
4. capacity_fade [folder] – Processed data 
4.1. G1C1.csv … G64C4.csv – Two-column tabular data for capacity fade curves of each 
cell. The first column is the time on test, and the second column is the remaining 
capacity. 
 
6 
5. Valid_cells.csv – CSV file contains the Cell ID for all the cells published in the current 
release. 
6. process_data.py – A sample code containing functions converting the RPT and the cycling 
JSON files to Python dictionaries. Also, this sample code provided processing functions to 
obtain the data for interpolated Q-V curves and capacity fade curves. 
This code is developed in the following environment: 
▪ python: 3.7.13 (Version 3.9.9 is compatible with packages below) 
▪ pandas: 1.3.5 
▪ scipy: 1.7.3 
▪ numpy: 1.21.5 
Note: An interpolation warning is triggered on line 164 for several cells when the assigned 
smoothing factor ("precision_C_5") is too low. Without intervention, this would result in 
an array of NaN for the variable "tck". To resolve this problem, lines 165-167 loops to 
correct the smoothing factor until the variable "tck" is no longer an array of NaN to ensure 
correct output. Therefore, you may ignore the warning. 
 
 
 
 
7 
4.2. Structure of RPT data 
 
 
 
G1C1.json
capacity_discharge_C_5
capacity_charge_C_5
Week 0
Week 0.5*
Week 1
Week 2
…
Python dictionary
Python list
Numpy array
capacity_discharge_C_2
capacity_discharge_C_2
QV_discharge_C_5
Q
0
0.5*
1
2
…
V
0
0.5*
1
2
…
E
0
0.5*
1
2
…
I
0
0.5*
1
2
…
t
0
0.5*
1
2
…
QV_charge_C_5
Same structure as QV_discharge_C_5
QV_discharge_C_2
Same structure as QV_discharge_C_5
QV_charge_C_2
Same structure as QV_discharge_C_5
start_stop_time
start
stop
Week 0
Week 0.5*
Week 1
Week 2
…
Week 0
Week 0.5*
Week 1
Week 2
…
Week 0
Week 0.5*
Week 1
Week 2
…
Week 0
Week 0.5*
Week 1
Week 2
…
Week 0
Week 0.5*
Week 1
Week 2
…
 
8 
4.3. Structure of cycling data 
 
 
G1C1.json
capacity_discharge
capacity_charge
Cycle 1
Cycle 2
Cycle 3
Cycle 4
…
Python dictionary
Python list
Numpy array
QV_discharge
Q
1
2
3
4
…
QV_charge
Same structure as QV_discharge
start
stop
Cycle 1
Cycle 2
Cycle 3
Cycle 4
…
V
1
2
3
4
…
E
1
2
3
4
…
I
1
2
3
4
…
t
1
2
3
4
…
start_stop_time
start
stop
time_series_discharge
Cycle 1
Cycle 2
Cycle 3
Cycle 4
…
Cycle 1
Cycle 2
Cycle 3
Cycle 4
…
time_series_charge
Same structure as time_series_discharge
Week 0.5*
Week 2
Week 3
…
Week 1
Week 0.5*
Week 2
Week 3
…
Week 1
 
9 
5. Acknowledgment 
The authors of this ISU-ILCC battery aging dataset acknowledge the support of Iowa Economic 
Development Authority under the Iowa Energy Center Grant No. 20-IEC-018. The authors also 
acknowledge the meaningful discussion on this dataset with Dr. David Howey and Zihao Zhou 
from University of Oxford. 
6. License 
This work is licensed under the Creative Commons Attribution (CC-BY) 4.0 International License. 
For more information visit: https://creativecommons.org/licenses/by/4.0. Please cite the associated  
7. Update for This Release 
• The dataset of 251 cells is fully released.  
• Table A1 is revised to include cycling conditions for G11. 
 
10 
Appendix 
A1.  Cycling conditions 
Group # 
Charging C-rate 
Discharging C-rate 
Mean DoD 
1 
0.500 
0.500 
25.90% 
2 
0.500 
0.500 
46.11% 
3 
0.500 
0.500 
67.77% 
4 
1.000 
0.500 
47.27% 
5 
1.000 
0.500 
97.54% 
6 
2.000 
0.500 
27.23% 
7 
2.000 
0.500 
46.86% 
8 
2.000 
0.500 
67.24% 
9 
2.000 
0.500 
96.93% 
10 
2.500 
0.500 
47.21% 
11 
2.500 
0.500 
95.98% 
12 
3.000 
0.500 
28.60% 
13 
3.000 
0.500 
47.26% 
14 
3.000 
0.500 
66.32% 
16 
0.500 
0.500 
97.62% 
17 
1.000 
0.500 
67.53% 
18 
2.500 
0.500 
27.53% 
19 
2.500 
0.500 
65.70% 
20 
0.800 
0.500 
98.16% 
21 
1.200 
0.500 
97.98% 
22 
1.400 
0.500 
97.88% 
23 
1.600 
0.500 
97.61% 
24 
1.800 
0.500 
97.51% 
25 
1.800 
0.600 
51.43% 
26 
1.400 
2.200 
4.16% 
27 
0.600 
2.400 
57.85% 
28 
2.400 
1.600 
80.99% 
29 
1.600 
1.800 
52.48% 
30 
0.800 
0.800 
77.59% 
31 
1.200 
1.000 
61.43% 
32 
1.000 
1.400 
38.86% 
33 
2.000 
1.200 
40.65% 
34 
2.200 
2.000 
27.60% 
35 
1.825 
0.500 
97.02% 
36 
2.075 
0.500 
97.06% 
37 
0.725 
0.500 
98.08% 
38 
1.875 
0.500 
95.83% 
39 
1.475 
0.500 
97.14% 
40 
1.825 
1.025 
31.94% 
41 
2.075 
1.775 
67.02% 
 
11 
Group # 
Charging C-rate 
Discharging C-rate 
Mean DoD 
42 
0.725 
2.375 
36.32% 
43 
1.875 
2.325 
38.00% 
44 
0.775 
1.275 
37.12% 
45 
1.125 
1.725 
80.26% 
46 
1.225 
2.025 
75.36% 
47 
2.325 
1.925 
48.27% 
48 
2.375 
2.225 
58.57% 
49 
0.975 
0.675 
18.82% 
50 
2.425 
1.625 
20.10% 
51 
2.275 
1.875 
53.64% 
52 
1.425 
0.875 
83.55% 
53 
2.025 
0.825 
91.54% 
54 
0.925 
1.125 
27.05% 
55 
1.025 
2.475 
61.44% 
56 
2.175 
0.975 
53.81% 
57 
1.775 
1.175 
17.42% 
58 
2.475 
0.575 
42.03% 
59 
1.325 
1.825 
31.64% 
60 
0.675 
1.325 
83.63% 
61 
2.125 
1.975 
54.07% 
62 
1.575 
2.425 
64.19% 
63 
1.975 
1.675 
80.57% 
64 
1.175 
1.425 
91.44% 
 
A2.  Notes for known abnormalities 
• For groups 20–29, we have unrecoverable data loss for the 4th week’s RPTs. During the 
data processing, all of the data was replaced by empty Python lists. 
• For cells G25C1, G26C1, G26C2, G26C3, and G26C4, we have unrecoverable data loss 
for the 23rd and 24th weeks’ RPTs, and the 24th week’s cycling tests.  
