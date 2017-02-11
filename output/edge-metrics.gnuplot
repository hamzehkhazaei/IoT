reset

monitor_file = 'monitor.txt'

# set terminal aqua size 625,250
set multiplot layout 3, 1 title "SAVI-IoT Platform -- Edges"
# set size ratio 0.39
set termoption dashed

# set xlabel "Time" font "Arial, 10"
set ytics nomirror
set y2tics
set tics font "Arial, 10"
set key font "Arial, 10" below


# set obj rectangle from 1881, graph 0 to 1900, graph 1    behind fillcolor rgb "#EEEEEE" fillstyle solid 1 noborder
# set obj rectangle from 1921, graph 0 to 1940, graph 1    behind fillcolor rgb "#EEEEEE" fillstyle solid 1 noborder
# set obj rectangle from 1961, graph 0 to 1980, graph 1    behind fillcolor rgb "#EEEEEE" fillstyle solid 1 noborder
# set obj rectangle from 1801, graph 0.98 to 2000, graph 1 behind fillcolor rgb "#2185F4" fillstyle solid 1 noborder


# use "dashtype 2" for dashed line
set style line  1 linewidth 2 linecolor rgb "#0060ad" linetype 1 # blue
set style line  2 linewidth 2 linecolor rgb "#dd181f" linetype 1 # red
set style line  3 linewidth 2 linecolor rgb "#008000" linetype 1 # green
set style line  4 linewidth 2 linecolor rgb "#FFA500" linetype 1 # orange
set style line  5 linewidth 2 linecolor rgb "#C849C3" linetype 1 # purple
set style line  6 linewidth 2 linecolor rgb "#FFE800" linetype 1 # yellow
set style line  7 linewidth 2 linecolor rgb "#C8A385" linetype 1 # 
set style line  8 linewidth 2 linecolor rgb "#5C402A" linetype 1 # 
set style line  9 linewidth 2 linecolor rgb "#F4E28A" linetype 1 # 
set style line 10 linewidth 2 linecolor rgb "#2185F4" linetype 1 # 
set style line 11 linewidth 2 linecolor rgb "#0060ad" linetype 1 dashtype 2 # blue
set style line 12 linewidth 2 linecolor rgb "#dd181f" linetype 2 dashtype 2 # red
set style line 13 linewidth 2 linecolor rgb "#008000" linetype 1 dashtype 2 # green
set style line 14 linewidth 2 linecolor rgb "#FFA500" linetype 1 dashtype 2 # orange
set style line 15 linewidth 2 linecolor rgb "#C849C3" linetype 1 dashtype 2 # purple
set style line 16 linewidth 2 linecolor rgb "#39B396" linetype 1 dashtype 2 # 
set style line 17 linewidth 2 linecolor rgb "#C8A385" linetype 1 dashtype 3 #
set style line 18 linewidth 2 linecolor rgb "#5C402A" linetype 1 dashtype 3 #
set style line 19 linewidth 2 linecolor rgb "#F4E28A" linetype 1 dashtype 3 # 
set style line 20 linewidth 2 linecolor rgb "#2185F4" linetype 1 dashtype 3 # 

set grid front y2tics layerdefault linetype 1 dt 4 linewidth 1.000 linecolor rgb "#999999"
 	 
# set obj rectangle from 0,0 to 12,12 behind fillcolor rgb "#CCCCCC" fillstyle solid 1 noborder
# set obj rectangle from 0,572 to 2000, 2000 behind fillcolor rgb "#E5A385" fillstyle solid 1 noborder

set xrange [0:180]
set xtics 10

set size 0.95, 0.32
set ylabel "VMs (#)" font "Arial, 10" offset 2
set y2label "Containers (#)" font "Arial, 10" offset -1
set format y "%2.0f"
set format y2 "%2.0f"
set ytics 1
set yrange [0:4]
set y2range [0:14]
set y2tics 2
plot    monitor_file using 3 with lines axis x1y1 linestyle 1 title "CG-Spark-VM", \
        monitor_file using 7 with lines axis x1y1 linestyle 2 title "CG-Kafka-VM", \
        monitor_file using 12 with lines axis x1y2 linestyle 11 title "CG-Spark-Cont", \
        monitor_file using 16 with lines axis x1y2 linestyle 12 title "CG-Kafka-Cont", \

set size 0.95, 0.32
set ylabel "VMs (#)" font "Arial, 10" offset 2
set y2label "Containers (#)" font "Arial, 10" offset -1
set format y "%2.0f"
set format y2 "%2.0f"
set ytics 1
set yrange [0:4]
set y2range [0:14]
set y2tics 2
plot    monitor_file using 4 with lines axis x1y1 linestyle 1 title "CT-Spark-VM", \
        monitor_file using 8 with lines axis x1y1 linestyle 2 title "CT-Kafka-VM", \
        monitor_file using 13 with lines axis x1y2 linestyle 11 title "CT-Spark-Cont", \
        monitor_file using 17 with lines axis x1y2 linestyle 12 title "CT-Kafka-Cont", \
                
set size 0.95, 0.32
set ylabel "VMs (#)" font "Arial, 10" offset 2
set y2label "Containers (#)" font "Arial, 10" offset -1
set format y "%2.0f"
set format y2 "%2.0f"
set ytics 1
set yrange [0:4]
set y2range [0:14]
set y2tics 2
plot    monitor_file using 5 with lines axis x1y1 linestyle 1 title "WT-Spark-VM", \
        monitor_file using 9 with lines axis x1y1 linestyle 2 title "WT-Kafka-VM", \
        monitor_file using 14 with lines axis x1y2 linestyle 11 title "WT-Spark-Cont", \
        monitor_file using 18 with lines axis x1y2 linestyle 12 title "WT-Kafka-Cont", \

unset multiplot
# pause 5
# reread
