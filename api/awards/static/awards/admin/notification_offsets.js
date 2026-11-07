(function ($) {
  function modeFor(eventVal) {
    if (eventVal === "voting_closing_reminder") return "close";
    if (eventVal === "eligibility_notice" || eventVal === "vote_invite")
      return "open";
    return null;
  }

  function findOffsetRows($row) {
    var $open = $row.find(".form-row.field-offset_minutes_before_open");
    var $close = $row.find(".form-row.field-offset_minutes_before_close");
    if (!$open.length) {
      $open = $row
        .find(".field-offset_minutes_before_open")
        .closest(".form-row, .fieldBox, .flex-container, .form-group");
    }
    if (!$close.length) {
      $close = $row
        .find(".field-offset_minutes_before_close")
        .closest(".form-row, .fieldBox, .flex-container, .form-group");
    }
    return { open: $open, close: $close };
  }

  function syncRow($row) {
    var $sel = $row.find('select[name="event"], select[name$="-event"]').first();
    if (!$sel.length) return;
    var mode = modeFor($sel.val());
    var rows = findOffsetRows($row);
    if (mode === "open") {
      rows.open.show();
      rows.close.hide();
    } else if (mode === "close") {
      rows.open.hide();
      rows.close.show();
    } else {
      rows.open.hide();
      rows.close.hide();
    }
  }

  function syncAll() {
    $("form").each(function () {
      var $form = $(this);
      if ($form.find('select[name="event"]').length) {
        syncRow($form);
      }
    });
    $(".inline-related").each(function () {
      syncRow($(this));
    });
  }

  $(function () {
    syncAll();
    $(document).on(
      "change",
      'select[name="event"], select[name$="-event"]',
      function () {
        syncRow($(this).closest(".inline-related, form"));
      }
    );
    $(document).on("formset:added", function (event, $row) {
      syncRow($row || $(event.target));
    });
  });
})(django.jQuery);
