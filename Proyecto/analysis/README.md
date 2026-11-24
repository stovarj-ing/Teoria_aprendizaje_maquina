# Análisis PM5300 — picos de potencia activa

Datos: `../data_zip.zip` (export de ThingsBoard, medidores 200 y 201).
Scripts y resultados de esta carpeta analizan la pregunta: **¿los picos de potencia activa son reales, ruido o un problema de adquisición?**

## Respuesta corta

Los picos son **eventos reales de carga**. No son ruido ni un registro corrupto.
La curva de 1 min del notebook los **exagera o los omite** porque `Resumen_*.csv` no es un promedio por minuto: es **una sola muestra** de 10 s (o 30 s) por minuto. Eso produce aliasing.
Los problemas de adquisición reales son otros: **huecos, cambios de cadencia y el registro de PF del medidor 201**.

## Evidencia principal

| Prueba | Resultado |
|---|---|
| `S = sqrt(3)·V·I` vs `apparent_power_total` (200) | error mediano 0.0007 kVA |
| `P_total = P_L1+P_L2+P_L3` (200) | error mediano 0.0000 kW |
| `PF = P/S` (200) | correlación 1.0000 |
| Integral de P (muestras cada 10 s) vs `Δ energy_import` | ratio mediano **0.9996** (0.04 %) |
| Tasa de eventos >2 kW sobre la base local | laboral **7.6/h**, fin de semana **1.0/h** |
| Contribución de los picos a la energía diaria | laboral **2.15 %**, fin de semana **0.48 %** |
| Carga base nocturna | **5.36 kW ≈ 128.7 kWh/día** |
| Energía diaria 24 h | laboral **169.8 kWh**, fin de semana **131.0 kWh** |

Ejemplo de evento real (10-08 19:16:48 UTC): P 9.1 → 14.9 kW durante **una muestra de 10 s**, corriente 37 → 49 A, PF 0.70 → 0.86, tensión 203.9 → 203.6 V, fases balanceadas (5.40/4.82/4.67 kW). Es una carga trifásica real, no un pico de un solo registro.

## Aliasing de la serie de 1 min

`Resumen` = una muestra por minuto, no un promedio:

- 10-08: coincide con la **primera** muestra de cada minuto (MAE 0, corr 1.0).
- 10-18: coincide con la **última** muestra de cada minuto (MAE 0, corr 1.0).
- 10-08 19:16: el pico real de 14.9 kW **no aparece** en el Resumen (9.29), porque se toma la primera muestra.
- 10-08 21:18: el pico real de 13.45 kW **sí aparece** en el Resumen, porque la primera muestra es el pico.
- En días con cadencia de 10 s, los picos del Resumen están 22–44 % por encima de la media real del minuto; en días de 30 s, 10–21 %.

Conclusión: para **picos** usar el `Analizador` (10 s); para **perfil** usar la **media** por minuto de los datos de 10 s, no el `Resumen` tal cual.

## Problemas de adquisición reales

| Día | Hueco interno (h) | Ventana local |
|---|---|---|
| 2026-10-22 | 8.36 | 11:44–20:06 |
| 2026-11-04 | 4.89 | 10:17–15:10 |
| 2026-10-20 | 4.24 | 07:20–11:34 |
| 2026-11-06 | 1.71 | 17:46–19:28 |
| 2026-10-07 | 1.19 | 12:15–13:26 |

- Cadencia: 10 s en 10-06…10-20; 30 s en 10-22…11-08; 83 s en 10-22; ~16 min en 11-01. La tasa de eventos no es comparable entre regímenes de muestreo.
- El medidor **201** tiene `power_factor > 1` en **29.068 de 29.085** muestras (99.94 %), hasta 1.60. No es un PF válido: no usarlo.
- El 201 tiene `P_L2 < 0` en 36 % de las muestras: revisar polaridad de TC / mapeo de fases.
- 5 timestamps duplicados en total; deduplicar.
- Faltan 10 días de calendario en `Resumen` (10-10…10-16, 10-21, 11-01, 11-02).

## Scripts

| Script | Qué hace |
|---|---|
| `load_resumen.py` | consolida los `Resumen` 200 y guarda `resumen200.pkl` |
| `compare_rules.py` | compara `Resumen` contra first/mean/last del `Analizador` |
| `align.py` | muestra el alineamiento exacto first/last por día |
| `energy_balance.py` | integral de P vs contador de energía |
| `event_rate.py` | tasa de eventos por día (laboral/fin de semana) |
| `inflation.py` | cuánto infla el Resumen los picos vs la media del minuto |
| `aliasing.py` | ejemplos de pico que se pierde y pico que se captura |
| `pf201.py` | diagnóstico del PF del 201 |
| `quality_scan.py` | duplicados, huecos, rangos, PF>1, P negativa |
| `final_stats.py` | carga base, PF, compensación reactiva |
| `top_windows.py` | ventanas de los eventos principales |
| `plot_alias.py` | genera `fig_aliasing.png` |
| `plot_event_rate.py` | genera `fig_rate_energy.png` |

## Reproducir

```powershell
cd repo\Proyecto
python analysis\load_resumen.py
python analysis\compare_rules.py
python analysis\energy_balance.py
python analysis\event_rate.py
python analysis\quality_scan.py
python analysis\plot_alias.py
python analysis\plot_event_rate.py
```
