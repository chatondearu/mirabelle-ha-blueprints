# Blind States

## Possible States

1. **Closed (0%)**
   - The blind is completely closed
   - The switch is OFF
   - Last action: complete closure

2. **Open (100%)**
   - The blind is completely open
   - The switch is OFF
   - Last action: complete opening

3. **Closing**
   - The blind is closing
   - The switch is ON
   - Last action: closing
   - Intermediate state

4. **Opening**
   - The blind is opening
   - The switch is ON
   - Last action: opening
   - Intermediate state

5. **Stopped in intermediate position**
   - The blind is stopped between 0% and 100%
   - The switch is OFF
   - Last action: stop
   - Intermediate state

## Switch Behavior

- **Switch action when blind is stopped**:
  - If the blind was closing → opening
  - If the blind was opening → closing
  - If the blind was closed → opening
  - If the blind was open → closing

- **Switch action during movement**:
  - Stop the blind
  - Remember current direction

## Special Features

- The blind automatically slows down:
  - Below 20% opening
  - Above 75% opening
- Complete travel time is the same for opening and closing
- Exact position is not known, it must be estimated based on time 