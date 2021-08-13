import { _ } from './gettext';

const CANCEL = 1,
      REMOVE = 2,
      RESTART = 3,
      RESIZE = 4,
      IMPORT = 5,
      PULL = 6;

let pendingActions = {
    [CANCEL]: {
        descr: _("Canceling...")
    },
    [REMOVE]: {
        descr: _("Deleting...")
    },
    [RESTART]: {
        descr: _("Restarting...")
    },
    [RESIZE]: {
      descr: _("Resizing images...")
    },
    [IMPORT]: {
      descr: _("Importing...")
    },
    [PULL]: {
      descr: _("Transferring images...")
    }
};

export default {
    CANCEL: CANCEL,
    REMOVE: REMOVE,
    RESTART: RESTART,
    RESIZE: RESIZE,
    IMPORT: IMPORT,
    PULL: PULL,

    description: function(pendingAction) {
      if (pendingActions[pendingAction]) return pendingActions[pendingAction].descr;
      else return "";
    }
};

