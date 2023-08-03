/*
Bootstable
 @description  Javascript library to make HMTL tables editable, using Bootstrap
 @version 1.1
 @autor Tito Hinostroza
*/
"use strict";
//Global variables
var params = null;  		//Parameters
var colsEdi =null;
var newColHtml = '<div class="btn-group pull-right">'+
'<button id="bEdit" type="button" class="btn btn-sm btn-default" onclick="butRowEdit(this);">' +
'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-pencil" viewBox="0 0 16 16"><path d="M12.146.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1 0 .708l-10 10a.5.5 0 0 1-.168.11l-5 2a.5.5 0 0 1-.65-.65l2-5a.5.5 0 0 1 .11-.168l10-10zM11.207 2.5 13.5 4.793 14.793 3.5 12.5 1.207 11.207 2.5zm1.586 3L10.5 3.207 4 9.707V10h.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.5h.293l6.5-6.5zm-9.761 5.175-.106.106-1.528 3.821 3.821-1.528.106-.106A.5.5 0 0 1 5 12.5V12h-.5a.5.5 0 0 1-.5-.5V11h-.5a.5.5 0 0 1-.468-.325z"/></svg>'+
'</button>'+
'<button id="bElim" type="button" class="btn btn-sm btn-default" onclick="butRowDelete(this);">' +
'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-trash3" viewBox="0 0 16 16"><path d="M6.5 1h3a.5.5 0 0 1 .5.5v1H6v-1a.5.5 0 0 1 .5-.5ZM11 2.5v-1A1.5 1.5 0 0 0 9.5 0h-3A1.5 1.5 0 0 0 5 1.5v1H2.506a.58.58 0 0 0-.01 0H1.5a.5.5 0 0 0 0 1h.538l.853 10.66A2 2 0 0 0 4.885 16h6.23a2 2 0 0 0 1.994-1.84l.853-10.66h.538a.5.5 0 0 0 0-1h-.995a.59.59 0 0 0-.01 0H11Zm1.958 1-.846 10.58a1 1 0 0 1-.997.92h-6.23a1 1 0 0 1-.997-.92L3.042 3.5h9.916Zm-7.487 1a.5.5 0 0 1 .528.47l.5 8.5a.5.5 0 0 1-.998.06L5 5.03a.5.5 0 0 1 .47-.53Zm5.058 0a.5.5 0 0 1 .47.53l-.5 8.5a.5.5 0 1 1-.998-.06l.5-8.5a.5.5 0 0 1 .528-.47ZM8 4.5a.5.5 0 0 1 .5.5v8.5a.5.5 0 0 1-1 0V5a.5.5 0 0 1 .5-.5Z"/></svg>'+
'</button>'+
'<button id="bAcep" type="button" class="btn btn-sm btn-default" style="display:none;" onclick="butRowAcep(this);">' +
'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-check" viewBox="0 0 16 16"><path d="M10.97 4.97a.75.75 0 0 1 1.07 1.05l-3.99 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425a.267.267 0 0 1 .02-.022z"/></svg>'+
'</button>'+
'<button id="bCanc" type="button" class="btn btn-sm btn-default" style="display:none;" onclick="butRowCancel(this);">' +
'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-x" viewBox="0 0 16 16"><path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/></svg>'+
'</button>'+
  '</div>';
  //Case NOT Bootstrap
  var newColHtml2 = '<div class="btn-group pull-right">'+
  '<button id="bEdit" type="button" class="btn btn-sm btn-default" onclick="butRowEdit(this);">' +
  '<span class="glyphicon glyphicon-pencil" > ✎ </span>'+
  '</button>'+
  '<button id="bElim" type="button" class="btn btn-sm btn-default" onclick="butRowDelete(this);">' +
  '<span class="glyphicon glyphicon-trash" > X </span>'+
  '</button>'+
  '<button id="bAcep" type="button" class="btn btn-sm btn-default" style="display:none;" onclick="butRowAcep(this);">' + 
  '<span class="glyphicon glyphicon-ok" > ✓ </span>'+
  '</button>'+
  '<button id="bCanc" type="button" class="btn btn-sm btn-default" style="display:none;" onclick="butRowCancel(this);">' + 
  '<span class="glyphicon glyphicon-remove" > → </span>'+
  '</button>'+
    '</div>';
var colEdicHtml = '<td name="buttons">'+newColHtml+'</td>'; 
$.fn.SetEditable = function (options) {
  var defaults = {
      columnsEd: null,         //Index to editable columns. If null all td editables. Ex.: "1,2,3,4,5"
      $addButton: null,        //Jquery object of "Add" button
      bootstrap: true,         //Indicates bootstrap is present.
      onEdit: function() {},   //Called after edition
      onBeforeDelete: function() {}, //Called before deletion
      onDelete: function() {}, //Called after deletion
      onAdd: function() {}     //Called when added a new row
  };
  params = $.extend(defaults, options);
  var $tabedi = this;   //Read reference to the current table.
  $tabedi.find('thead tr').append('<th name="buttons"></th>');  //Add empty column
  if (!params.bootstrap) {
    colEdicHtml = '<td name="buttons">'+newColHtml2+'</td>'; 
  }
  //Add column for buttons to all rows.
  $tabedi.find('tbody tr').append(colEdicHtml);
  //Process "addButton" parameter
  if (params.$addButton != null) {
      //There is parameter
      params.$addButton.click(function() {
          rowAddNew($tabedi.attr("id"));
      });
  }
  //Process "columnsEd" parameter
  if (params.columnsEd != null) {
      //Extract felds
      colsEdi = params.columnsEd.split(',');
  }
};
function IterarCamposEdit($cols, action) {
//Iterate through editable fields in a row
  var n = 0;
  $cols.each(function() {
      n++;
      if ($(this).attr('name')=='buttons') return;  //Exclude buttons column
      if (!IsEditable(n-1)) return;   //It's not editable
      action($(this));
  });
  
  function IsEditable(idx) {
  //Indicates if the passed column is set to be editable
      if (colsEdi==null) {  //no se definió
          return true;  //todas son editable
      } else {  //hay filtro de campos
          for (var i = 0; i < colsEdi.length; i++) {
            if (idx == colsEdi[i]) return true;
          }
          return false;  //no se encontró
      }
  }
}
function ModoEdicion($row) {
  if ($row.attr('id')=='editing') {
      return true;
  } else {
      return false;
  }
}
//Set buttons state
function SetButtonsNormal(but) {
  $(but).parent().find('#bAcep').hide();
  $(but).parent().find('#bCanc').hide();
  $(but).parent().find('#bEdit').show();
  $(but).parent().find('#bElim').show();
  var $row = $(but).parents('tr');  //accede a la fila
  $row.attr('id', '');  //quita marca
}
function SetButtonsEdit(but) {
  $(but).parent().find('#bAcep').show();
  $(but).parent().find('#bCanc').show();
  $(but).parent().find('#bEdit').hide();
  $(but).parent().find('#bElim').hide();
  var $row = $(but).parents('tr');  //accede a la fila
  $row.attr('id', 'editing');  //indica que está en edición
}
//Events functions
function butRowAcep(but) {
//Acepta los cambios de la edición
  var $row = $(but).parents('tr');  //accede a la fila
  var $cols = $row.find('td');  //lee campos
  if (!ModoEdicion($row)) return;  //Ya está en edición
  //Está en edición. Hay que finalizar la edición
  IterarCamposEdit($cols, function($td) {  //itera por la columnas
    var cont = $td.find('input').val(); //lee contenido del input
    $td.html(cont);  //fija contenido y elimina controles
  });
  SetButtonsNormal(but);
  params.onEdit($row);
}
function butRowCancel(but) {
//Rechaza los cambios de la edición
  var $row = $(but).parents('tr');  //accede a la fila
  var $cols = $row.find('td');  //lee campos
  if (!ModoEdicion($row)) return;  //Ya está en edición
  //Está en edición. Hay que finalizar la edición
  IterarCamposEdit($cols, function($td) {  //itera por la columnas
      var cont = $td.find('div').html(); //lee contenido del div
      $td.html(cont);  //fija contenido y elimina controles
  });
  SetButtonsNormal(but);
}
function butRowEdit(but) {  
  //Start the edition mode for a row.
  var $row = $(but).parents('tr');  //accede a la fila
  var $cols = $row.find('td');  //lee campos
  if (ModoEdicion($row)) return;  //Ya está en edición
  //Pone en modo de edición
  var focused=false;  //flag
  IterarCamposEdit($cols, function($td) {  //itera por la columnas
      var cont = $td.html(); //lee contenido
      //Save previous content in a hide <div>
      var div  = '<div style="display: none;">' + cont + '</div>';  
      var input= '<input class="form-control input-sm"  value="' + cont + '">';
      $td.html(div + input);  //Set new content
      //Set focus to first column
      if (!focused) {
        $td.find('input').focus();
        focused = true;
      }
  });
  SetButtonsEdit(but);
}
function butRowDelete(but) {  //Elimina la fila actual
  var $row = $(but).parents('tr');  //accede a la fila
  params.onBeforeDelete($row);
  $row.remove();
  params.onDelete();
}
//Functions that can be called directly
function rowAddNew(tabId, initValues=[], classnames= []) {
  /* Add a new row to a editable table. 
   Parameters: 
    tabId       -> Id for the editable table.
    initValues  -> Optional. Array containing the initial value for the 
                   new row.
  */
  var $tab_en_edic = $("#"+tabId);  //Table to edit
  var $rows = $tab_en_edic.find('tbody tr');
  //if ($rows.length==0) {
      //No hay filas de datos. Hay que crearlas completas
      var $row = $tab_en_edic.find('thead tr');  //encabezado
      var $cols = $row.find('th');  //lee campos
      //construye html
      var htmlDat = '';
      var i = 0;
      $cols.each(function() {
          if ($(this).attr('name')=='buttons') {
              //Es columna de botones
              htmlDat = htmlDat + colEdicHtml;  //agrega botones
          } else {
              if (i<initValues.length) {
                htmlDat = htmlDat + '<td class="' + classnames[i] + '">'+initValues[i]+'</td>';
              } else {
                htmlDat = htmlDat + '<td class="' + classnames[i] + '"></td>';
              }
          }
          i++;
      });
      $tab_en_edic.find('tbody').append('<tr>'+htmlDat+'</tr>');
  /*} else {
      //Hay otras filas, podemos clonar la última fila, para copiar los botones
      var $lastRow = $tab_en_edic.find('tr:last');
      $lastRow.clone().appendTo($lastRow.parent());  
      $lastRow = $tab_en_edic.find('tr:last');
      var $cols = $lastRow.find('td');  //lee campos
      $cols.each(function() {
          if ($(this).attr('name')=='buttons') {
              //Es columna de botones
          } else {
              $(this).html('');  //limpia contenido
          }
      });
  }*/
  params.onAdd();
}
function rowAddNewAndEdit(tabId, initValues=[], classnames= []) {
/* Add a new row an set edition mode */  
  rowAddNew(tabId, initValues, classnames);
  var $lastRow = $('#'+tabId + ' tr:last');
  butRowEdit($lastRow.find('#bEdit'));  //Pass a button reference
}
function TableToCSV(tabId, separator) {  //Convert table to CSV
  var datFil = '';
  var tmp = '';
  var $tab_en_edic = $("#" + tabId);  //Table source
  $tab_en_edic.find('tbody tr').each(function() {
      //Termina la edición si es que existe
      if (ModoEdicion($(this))) {
          $(this).find('#bAcep').click();  //acepta edición
      }
      var $cols = $(this).find('td');  //lee campos
      datFil = '';
      $cols.each(function() {
          if ($(this).attr('name')=='buttons') {
              //Es columna de botones
          } else {
              datFil = datFil + $(this).html() + separator;
          }
      });
      if (datFil!='') {
          datFil = datFil.substr(0, datFil.length-separator.length); 
      }
      tmp = tmp + datFil + '\n';
  });
  return tmp;
}
function TableToJson(tabId) {   //Convert table to JSON
  var json = '{';
  var otArr = [];
  var tbl2 = $('#'+tabId+' tr').each(function(i) {        
     var x = $(this).children();
     var itArr = [];
     x.each(function() {
        itArr.push('"' + $(this).text() + '"');
     });
     otArr.push('"' + i + '": [' + itArr.join(',') + ']');
  })
  json += otArr.join(",") + '}'
  return json;
}