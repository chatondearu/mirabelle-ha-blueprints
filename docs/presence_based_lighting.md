# Éclairage basé sur la présence

Ce blueprint permet de contrôler automatiquement l'éclairage en fonction de la détection de présence.

## Prérequis

- Un capteur de présence (binary_sensor)
- Une ou plusieurs lumières à contrôler

## Configuration

1. Importez le blueprint dans Home Assistant
2. Créez une nouvelle automatisation en utilisant ce blueprint
3. Configurez les paramètres suivants :
   - **Presence Sensor** : Sélectionnez votre capteur de présence
   - **Light to Control** : Sélectionnez la lumière à contrôler
   - **Delay Before Turning Off** : Définissez le délai avant l'extinction (en secondes)

## Fonctionnement

- La lumière s'allume automatiquement lorsque la présence est détectée
- La lumière s'éteint automatiquement après le délai configuré lorsque la présence n'est plus détectée

## Personnalisation

Vous pouvez modifier les paramètres suivants :
- Le délai d'extinction (entre 0 et 3600 secondes)
- Le type de capteur de présence
- Les lumières à contrôler

## Exemples d'utilisation

1. **Couloir** : Allumage automatique lors du passage, extinction après 5 minutes
2. **Salle de bain** : Allumage à l'entrée, extinction après 10 minutes
3. **Bureau** : Allumage à l'entrée, extinction immédiate à la sortie 