<?php
// Las preguntas de la consulta sobre la Colección Monte Verde (encuesta.html).
//
// De aquí sacan lo que necesitan la recepción (encuesta.php: qué valores se aceptan) y
// el panel (index.php: cómo se resume cada una). El formulario de encuesta.html usa las
// mismas claves: si se cambia una pregunta, se cambia en los dos lados.
//
// Tipos:  una      una sola opción                varias   ninguna, una o varias
//         nota     de 1 a 5                        texto    una línea libre
//         palabras hasta tres palabras sueltas
declare(strict_types=1);

const SI_NO = ['si' => 'Sí', 'no' => 'No'];

// clave => [tipo, pregunta, opciones, obligatoria]. El texto es el de la consulta que
// entregó el proyecto, tal cual.
const PREGUNTAS = [
    'visito'         => ['una', '1. ¿Ha visitado físicamente el sitio arqueológico Monte Verde?', SI_NO, true],
    'vio_objetos'    => ['una', '2. ¿Ha visto objetos arqueológicos provenientes de este sitio?', SI_NO, true],
    'como_vio'       => ['una', '3. ¿Los ha visto físicamente o representados en fotografías / ilustraciones?',
                         ['fisicamente' => 'Físicamente', 'imagen' => 'Imagen'], false],
    'cuanto_sabe'    => ['nota', '4. ¿Cuánto sabe sobre el sitio Monte Verde?', null, true],
    'registro'       => ['varias', '5. El sitio Monte Verde posee un registro arqueológico compuesto por:',
                         ['megafauna' => 'Huesos de megafauna', 'piedra' => 'Herramientas de piedra',
                          'madera' => 'Herramientas de madera', 'fibras' => 'Herramientas de fibras vegetales',
                          'cuero' => 'Cuero y/o restos de carne'], false],
    'cuantas_piezas' => ['una', '6. ¿Sabe cuántas piezas componen la colección Monte Verde?',
                         ['0-100' => '0 a 100', '100-1000' => '100 a 1.000', 'mas-1000' => 'Más de 1.000'], true],
    'museo'          => ['una', '7. ¿Cree necesario que Puerto Montt cuente con un Museo especializado en poblamiento antiguo?', SI_NO, true],
    'museo_donde'    => ['texto', '8. Si está de acuerdo ¿Dónde debiese estar este Museo?', null, false],
    'identidad'      => ['una', '9. ¿Cree que Monte Verde forma parte de la identidad cultural de Puerto Montt?', SI_NO, true],
    'falta_espacios' => ['una', '10. ¿Cree que aún falta incorporar elementos del sitio Monte Verde en los espacios públicos de Puerto Montt y la comuna?', SI_NO, true],
    'espacios_donde' => ['texto', '10. Si es así, ¿dónde?', null, false],
    'nota_visita'    => ['nota', '11. Califique la experiencia de la visita a la Colección Monte Verde, escala 1 a 5', null, true],
    'palabras'       => ['palabras', '12. Escriba 3 palabras o conceptos sobre la experiencia que ha vivido hoy', null, true],
];
