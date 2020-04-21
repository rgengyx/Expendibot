#!/bin/sh

opponents=( $2 )

for opponent in "${opponents[@]}"; do

  num_games=$1
  white_win=0
  black_win=0
  draw=0

  for ((i=0; i<$num_games; i=i+1)); do

    win=$(python3.6 -m referee rapidbot $opponent | grep winner)
    winner=${win:10:5}

    if [[ $winner == "white" ]]; then
      let "white_win+=1"
    elif [[ $winner == "black" ]]; then
      let "black_win+=1"
    else
      let "draw+=1"
    fi
    echo -n "#"
  done
  echo
  win_rate=$(bc<<<"scale=3;$white_win/$num_games")
  echo "Win rate against $opponent = $win_rate   |   win $white_win, lose $black_win, draw $draw"
done