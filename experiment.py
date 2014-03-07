#!/usr/bin/python

def addAnswer(answers, quality, reply ):
    if quality not in answers.keys():
        answers[quality] = ''
    answers[quality] += reply

# test script for experimentation

Qt = int(raw_input("Calidad Qt?"))
Qi = int(raw_input("Calidad Qi?"))
qualities=[10,20,30,40,50,60,70,80,90,100]
QMax=100
QMin=10

# beware, Qi could be greater than Qt
stepSize = abs((Qt - Qi) / 2)
reversals = 0

# we need "proportion of correct responses"
# we are interested in PSE, so the stopping criteria
# will be after a number of reversals on the 50% correct
# choices. This means that the participant cannot really
# distinguish with certainty between the two stimuli.
# After the first reversal, the method will be Up/Down and
# the step size 1 for both cases.
# After 10 reversals (wrong answers) Qt is changed.

targetPos = 'left'
answers = {}
# because we start with Qi far away, assume a correct answer.
last_answer = None

while reversals < 10:
    answer = raw_input("Which option is best, left or right?")
    # correct answer, get closer to Qt
    if answer in targetPos:
        if last_answer is not None and last_answer == 0:
            reversals += 1
        last_answer = 1
        # always stepSize is smaller (or 1) than abs(Qt-Qi)
        addAnswer(answers, Qi, '1')
        if Qi < Qt:
            Qi = min(Qi + stepSize, QMax)
            if Qi == Qt:
                Qi -= 1
        else:
            Qi = max(Qi - stepSize, QMin)
            if Qi == Qt:
                Qi += 1
    # incorrect
    else:
        if last_answer is not None and last_answer == 1:
            reversals += 1
        last_answer = 0
        # always stepSize is smaller (or 1) than abs(Qt-Qi)
        addAnswer(answers, Qi, '0')
        if Qi < Qt:
            Qi = min(Qi + stepSize, QMax)
            if Qi == Qt:
                Qi -= 1
        else:
            Qi = max(Qi - stepSize, QMin)
            if Qi == Qt:
                Qi += 1
    stepSize = max(stepSize/2,1)
    print Qt, Qi


