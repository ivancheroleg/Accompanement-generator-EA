import mido
import music21
import random

"""
To run this program you need to install music21 and mido libraries.
Also, you need to clarify name for the input file in to commands lower for mido read and music21 converter.parse.
and at the end of the program to clarify output.
"""


midFile = mido.MidiFile('input1.mid', clip=True)  # Can change input name


"""Detecting key with usage of music21 library"""
key = music21.converter.parse('input1.mid').analyze(
    'key')  # Can change input name


"""
Chord class

Represents a chord with a root note and a type of chord:
minor, major or diminished
"""


class Chord:

    def __init__(self, rootNote, chordType):
        # root note of the chord
        self.rootNote = rootNote
        # type of the chord
        self.chordType = chordType

        # 'Builder' for for the chord with its type.
        if chordType == 'major':
            self.notes = [rootNote %
                          12, (rootNote + 4) % 12, (rootNote + 7) % 12]
        elif chordType == 'minor':
            self.notes = [rootNote %
                          12, (rootNote + 3) % 12, (rootNote + 7) % 12]
        elif chordType == 'diminished':
            self.notes = [rootNote %
                          12, (rootNote + 3) % 12, (rootNote + 6) % 12]


"""
Accompaniment class

Input: key of the song
Output: list of chords

This class is used to generate/contain accompaniment for the song.
depending on the key of the song, it generates chords for the accompaniment.
"""


class Accompaniment:

    def __init__(self, key):

        # Scale depends on the key of the song
        if (key.mode == "major"):
            keyNoteScale = key.tonic.midi % 12
        else:
            keyNoteScale = (key.tonic.midi + 3) % 12

        # List of chords for the accompaniment
        self.chords = [
            Chord(keyNoteScale % 12, 'major'),
            Chord((keyNoteScale + 5) % 12, 'major'),
            Chord((keyNoteScale + 7) % 12, 'major'),
            Chord((keyNoteScale + 9) % 12, 'minor'),
            Chord((keyNoteScale + 2) % 12, 'minor'),
            Chord((keyNoteScale + 4) % 12, 'minor'),
            Chord((keyNoteScale + 11) % 12, 'diminished')
        ]


"""Method returns amount of notes in the track"""


def getAmountOfNotes(mid):
    beats = sum(x.time for x in mid.tracks[1] if type(x) is mido.Message)
    return (beats + mid.ticks_per_beat*2 - 1) // (mid.ticks_per_beat*2)


"""Getting tempo of the track"""
tempo = [x.tempo for x in midFile.tracks[0] if x.type == 'set_tempo'][0]
accompanimentPart = [mido.MetaMessage('set_tempo', tempo=tempo, time=0)]


"""Computation of the beats"""
notes = [None]*getAmountOfNotes(midFile)
chordSpace = midFile.ticks_per_beat*2

beats = 0
lastNote = 0

for message in midFile.tracks[1]:
    typemsg = message.type
    if (typemsg == "note_off"):
        lastNote = message.note

    elif (beats % chordSpace == 0 and typemsg == "note_on"):
        if (notes[beats // chordSpace] is None):
            notes[beats // chordSpace] = message.note

    beats += message.time

if (beats % chordSpace == 0):
    notes[-1] = lastNote


# Initialize accompaniment
finGenChord = Accompaniment(key)
maxNote = 120  # limitation of the notes in the track

"""
Class Chromosome

Input: size of the chromosome

Represents a chromosome with a list of genes
"""


class Chromosome:
    def __init__(self, size):

        self.size = size
        self.fitness = 0
        self.genesPool = [None]*size

        for i in range(self.size):

            rand_note = random.randint(0, maxNote)
            rand_chord = Chord(rand_note, random.choice(
                ['major', 'minor', 'diminished']))
            self.genesPool[i] = rand_chord


"""
Fitness function.
Input: population
"""


def fitnessFunction(population):
    for chrom in population:
        chrom.fitness = chrom.size*2

        for x in range(chrom.size):

            # Check for chord to be consonant
            isChordInPool = False
            for chord in finGenChord.chords:
                if chord.rootNote == chrom.genesPool[x].rootNote and chord.chordType == chrom.genesPool[x].chordType:
                    isChordInPool = True

            if isChordInPool:

                chrom.fitness -= 1

                # Chord is none => consonant chord may fit in
                if (notes[x] is None):
                    chrom.fitness -= 1
                    continue

                # Note in consonant chord and in melody. or not.
                isNoteInChord = True
                for chord in finGenChord.chords:
                    if (notes[x] % 12 in chord.notes):
                        isNoteInChord = False

                isNoteInPool = False
                if (notes[x] % 12 in chrom.genesPool[x].notes):
                    isNoteInPool = True

                if (isNoteInChord or isNoteInPool):
                    chrom.fitness -= 1


# Creating population
populationSize = 256
survivors = [None] * 32
population = [Chromosome(getAmountOfNotes(midFile))
              for _ in range(populationSize)]


"""
Cross method for the chromosomes
Input: two chromosomes
Take two chromosomes and cross their chords
"""


def cross(chrom1, chrom2):
    childChrom = Chromosome(chrom1.size)
    point = random.randint(0, chrom1.size - 1)
    for i in range(point):
        childChrom.genesPool[i] = chrom1.genesPool[i]
    for i in range(point, chrom1.size):
        childChrom.genesPool[i] = chrom2.genesPool[i]
    return childChrom


"""
Method repopulate with deciding 2 random chromosomes-parents each iteration
"""


def repopulate(population, parents, count):
    while count < len(population):
        # 1 parent Chromosome
        parent1 = random.randint(0, len(parents) - 1)
        # 2 parent Chromosome
        while True:
            index = random.randint(0, len(parents) - 1)
            if index != parent1:
                parent2 = index
                break
        # Cross
        population[count] = cross(parents[parent1], parents[parent2])
        population[count + 1] = cross(parents[parent2], parents[parent1])
        count += 2


"""
Method to mutate a chromosome
"""


def mutate(population, chromCount):
    for _ in range(chromCount):

        chromPos = random.randint(0, len(population) - 1)
        chromo = population[chromPos]
        for __ in range(1):

            chromo.genesPool[random.randint(0, chromo.size - 1)] = Chord(
                random.randint(0, maxNote), random.choice(
                    ['major', 'minor', 'diminished']))


iter = 0
iterLimit = 10000

while True:
    iter += 1

    # Calculate fitness values for each chromosome and then sort them
    fitnessFunction(population)
    population = sorted(population, key=lambda x: x.fitness)

    # If the best chromosome is perfect, we're done or if we reached the iteration limit
    if (population[0].fitness == 0 or iter == iterLimit):
        break

    # Selecting the best chromosomes
    for i in range(len(survivors)):
        survivors[i] = population[i]
    # Repopulate
    repopulate(population, survivors, populationSize//2)
    mutate(population,  len(population)//2)


"""Calculating average velocity of notes"""
sumVelocity = sum(
    [x.velocity for x in midFile.tracks[1] if x.type == 'note_on'])
velocity = int(0.9 * sumVelocity /
               sum([1 for x in midFile.tracks[1] if x.type == 'note_on']))


"""Calculating displacement with average octave"""
sumOctave = sum([x.note//12 for x in midFile.tracks[1] if x.type == 'note_on'])
shift = 12 * \
    int(sumOctave /
        sum([1 for x in midFile.tracks[1] if x.type == 'note_on']) - 1)


for chord in population[0].genesPool:

    accompanimentPart.append(mido.Message(
        'note_on', note=chord.notes[0] + shift, velocity=velocity, time=0))
    accompanimentPart.append(mido.Message(
        'note_on', note=chord.notes[1] + shift, velocity=velocity, time=0))
    accompanimentPart.append(mido.Message(
        'note_on', note=chord.notes[2] + shift, velocity=velocity, time=0))
    accompanimentPart.append(mido.Message(
        'note_off', note=chord.notes[0] + shift, velocity=velocity, time=midFile.ticks_per_beat*2))
    accompanimentPart.append(mido.Message(
        'note_off', note=chord.notes[1] + shift, velocity=velocity, time=0))
    accompanimentPart.append(mido.Message(
        'note_off', note=chord.notes[2] + shift, velocity=velocity, time=0))

"""Output. Generating midi file and its name"""
midFile.tracks.append(accompanimentPart)
strKey = str(key)
# Change this string to change the name of the output file
str = "IvanChernakovOutput1111-"
str += strKey[0].upper()
if strKey.find('minor') != -1:
    str += strKey[1:-6:] + "m"

midFile.save(str + '.mid')
