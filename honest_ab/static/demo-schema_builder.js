$(document).ready(function() {
  var schemaContainer = $("#create-demo_schema-container");
  var addFieldButton = schemaContainer.find(".js-add_schema_field");

  var fieldCount = 0;

  function addField() {
    var row = $("<div />");
    var id = fieldCount;
    row.attr("id", id);
    row.attr("class", "schema-creator-row");

    var fieldName = $("<input />");
    fieldName.attr("name", "schema_field_" + id + "_name");
    fieldName.attr("placeholder", "Field Name");
    fieldName.attr("class", "form-control schema-creator-field");
    row.append(fieldName);

    var fieldType = $("<select />");
    fieldType.attr("name", "schema_field_" + id + "_type");
    fieldType.attr("class", "form-control schema-creator-field");
    [["Numeric", "numeric"]].forEach(function(value_display_name) {
      var option = $("<option />");
      option.html(value_display_name[0]);
      option.attr("value", value_display_name[1]);
      fieldType.append(option);
    });
    row.append(fieldType);

    ["A", "B"].forEach(function(variant) {
      var variantCorrelation = $("<select />");
      variantCorrelation.attr("name", "schema_field_" + id + "_correlation_" + variant);
      variantCorrelation.attr("class", "form-control schema-creator-field");
      var header = $("<option disabled selected hidden />");
      header.html(variant + " Correlation");
      header.attr("value", "");
      variantCorrelation.append(header);
      [
        ["Positive-Nonlinear", "+n"],
        ["Positive-Linear", "+l"],
        ["Independent", "+i"],
        ["Negative-Linear", "-l"],
        ["Negative-Nonlinear", "-n"],
      ].forEach(function(value_display_name) {
        var option = $("<option />");
        option.html(value_display_name[0]);
        option.attr("value", value_display_name[1]);
        variantCorrelation.append(option);
      });
      row.append(variantCorrelation);
    });

    var removeButton = $("<div />");
    removeButton.html("Delete");
    removeButton.attr("class", "btn btn-primary schema-creator-field");
    removeButton.click(function() {
      row.remove();
      fieldCount -= 1;
    });
    row.append(removeButton);

    row.insertBefore(addFieldButton);
    fieldCount += 1;
  }

  addFieldButton.click(function() {
    addField();
  });

  addField();
});
