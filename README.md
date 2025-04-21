--- this project is made compatable with ros 2 and linux 20.04 

---commands to edit the files 

cd ~/ros2_ws/src/tic_tac_toe/tic_tac_toe


touch tic_tac_toe_ros.py



gedit  tic_tac_toe_ros.py


chmod +x tic_tac_toe_ros.py


cd ~/ros2_ws/src/tic_tac_toe

gedit  setup.py


--- commands to run the project 
cd ~/ros2_ws

colcon build --packages-select tic_tac_toe

source ~/ros2_ws/install/setup.bash

ros2 run tic_tac_toe tic_tac_toe_ros
