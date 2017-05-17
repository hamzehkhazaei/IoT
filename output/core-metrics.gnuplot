reset
monitor_file = 'monitor-exp1.txt'
rt_monitor_file = 'rt_monitor-exp1.txt'

# set terminal aqua size 625,250
set multiplot layout 3, 1 # title "SAVI-IoT Platform -- CORE"
set termoption dashed

# set xlabel "Time" font "Arial, 10"
set ytics nomirror
set tics font "Arial, 12"
set key font "Arial, 12" below


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

set grid front ytics layerdefault linetype 1 dt 4 linewidth 1.000 linecolor rgb "#999999"
 	 
# set obj rectangle from 0,0 to 12,12 behind fillcolor rgb "#CCCCCC" fillstyle solid 1 noborder
# set obj rectangle from 0,572 to 2000, 2000 behind fillcolor rgb "#E5A385" fillstyle solid 1 noborder

set xrange [0:150]
set xtics 10

set size 0.91, 0.3
set ylabel "VMs (#)" font "Arial, 12" offset 2
set format y "%3.0f"
set ytics 1
set yrange [0:4]
plot    monitor_file using 2 with lines axis x1y1 linestyle 1 title "CORE-Spark-VM", \
        monitor_file using 6 with lines axis x1y1 linestyle 2 title "CORE-Kafka-VM", \
        monitor_file using 10 with lines axis x1y1 linestyle 3 title "CORE-Cassandra-VM", \
        
set size 0.91, 0.3
set ylabel "Containers (#)" font "Arial, 12" offset 2
set format y "%3.0f"
set ytics 2
set yrange [0:14]
plot    monitor_file using 11 with lines axis x1y1 linestyle 11 title "CORE-Spark-Cont", \
        monitor_file using 15 with lines axis x1y1 linestyle 12 title "CORE-Kafka-Cont", \
        monitor_file using 19 with lines axis x1y1 linestyle 13 title "CORE-Cassandra-Cont", \


set xrange [30:70]
set size 0.99, 0.33
set boxwidth 0.2
set style fill solid
set ylabel "VM-RT (sec)" font "Arial, 12" offset 2
set y2label "Cont-RT (ms)" font "Arial, 12" offset -1
set format y "%2.0f"
set yrange [0:300]
set ytics 50
set y2range [0:600]
set y2tics 100
set xtics border in scale 0,0 nomirror rotate by -45  autojustify font "Arial, 12"
set xtics  norangelimit 
set xtics   ()
        
plot    rt_monitor_file using 2:xtic(4) with boxes axis x1y1 title "Macroservice Provisioning Time", \
        rt_monitor_file using ($3)*1000:xtic(5) with boxes axis x1y2 title "Microservice Provisioning Time", \

        
unset multiplot
# pause 7
# reread
