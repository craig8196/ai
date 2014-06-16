start call startagents.bat
python bin/bzrflag --friendly-fire \
--red-port=50100 --green-port=50101 --purple-port=50102 --blue-port=50103 \
--default-posnoise=3 \
--time-limit=240 --max-shots=3 --respawn-time=240 \
--seed=0 --world="maps/four_ls.bzw" --window-size=580x580 \
--green-tanks=4 --purple-tanks=4 --red-tanks=0 --blue-tanks=0 \
--default-true-positive=.97 --default-true-negative=.9 --occgrid-width=100 --no-report-obstacles $@ &

sleep 2

python bzagents/final_agent.py localhost 50102 
#~ python bzagents/final_agent.py localhost 50101 &
