# LLMDTP_V2


#### step 1 ####
# Please install the environment first with conda by running the following code in the terminal, and enter the environment
conda create -n embedding python=3.10 -y
conda activate embedding

#### step 2 ####
# And install the following packets
pip install streamlit requests

#### step 3 ####
modify the function sent_to_llm() in the new_DTP_exam_real.py to your own api to using llm

#### step 3 ####
# Start the streamlit service
# run the following code
nohup streamlit run new_DTP_exam_real.py &
